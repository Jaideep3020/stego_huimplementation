"""Audit-backed experiment runner and C1–C4 aggregation."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
import yaml

from .io_chaos import DEFAULT_DATA, audit
from .metrics import confusion, from_confusion
from .pipeline import segment_slice

METRICS = ['dice', 'miou', 'iou_liver', 'iou_bg']


def write_json(path, value):
    def clean(v):
        if isinstance(v, dict):
            return {str(k): clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        if isinstance(v, np.generic):
            v = v.item()
        return None if isinstance(v, float) and not np.isfinite(v) else v
    Path(path).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n')


def versions():
    import platform
    names = ['numpy', 'scipy', 'scikit-image', 'pydicom', 'pandas', 'matplotlib', 'pyyaml', 'Pillow', 'opencv-python-headless']
    import cv2
    result = {'python': platform.python_version(), 'opencv_runtime': cv2.__version__}
    for name in names:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    return result


def median_volume(cache, patient, k):
    path = Path(cache) / f'{patient}_med{k}.npy'
    hu = np.load(Path(cache) / f'{patient}_hu.npy', mmap_mode='r')
    if k <= 1:
        return hu
    if not path.exists():
        target = np.lib.format.open_memmap(path.with_suffix('.partial.npy'), mode='w+', dtype=np.float32, shape=hu.shape)
        for i, image in enumerate(hu):
            target[i] = ndi.median_filter(image, size=k, mode='reflect')
        target.flush()
        del target
        path.with_suffix('.partial.npy').replace(path)
    return np.load(path, mmap_mode='r')


def evaluate_patient(task):
    """Predict one patient with the fixed paper configuration and count errors."""
    cache, meta, cfg, backend = task
    if backend == 'opencv':
        import cv2
        cv2.setNumThreads(1)
    patient = meta['patient']
    gt = np.load(Path(cache) / f'{patient}_gt.npy', mmap_mode='r')
    filtered = median_volume(cache, patient, cfg['med_k'])
    rows, totals = [], np.zeros(4, dtype=np.int64)
    for index, (image, ground_truth) in enumerate(zip(filtered, gt)):
        prediction = segment_slice(image, **cfg, backend=backend, prefiltered=True)
        counts = confusion(prediction, ground_truth)
        totals += counts
        rows.append(dict(patient=patient, slice=index,
                         gt_voxels=int(np.count_nonzero(ground_truth)),
                         pred_voxels=int(np.count_nonzero(prediction)),
                         tp=counts[0], fp=counts[1], fn=counts[2], tn=counts[3],
                         **from_confusion(*counts)))
    summary = dict(patient=patient, slices=len(gt), tp=int(totals[0]), fp=int(totals[1]),
                   fn=int(totals[2]), tn=int(totals[3]), **from_confusion(*map(int, totals)))
    return summary, rows


def describe(table, metrics):
    return {k: dict(mean=float(table[k].mean()), std=float(table[k].std(ddof=0)), n=int(table[k].notna().sum())) for k in metrics}


def aggregate(per_patient, per_slice):
    """Headline scores weight patients equally; secondary summaries are labelled."""
    totals = per_patient[['tp', 'fp', 'fn', 'tn']].sum().to_numpy()
    return dict(C1=describe(per_patient, METRICS),
                C2=describe(per_slice, METRICS),
                C3=describe(per_slice[per_slice.gt_voxels > 0], METRICS),
                C4=from_confusion(*map(int, totals)),
                patients=len(per_patient), slices=len(per_slice),
                conventions={'headline': 'C1: per-patient whole-volume scores, then mean over patients',
                             'std': 'Population SD (ddof=0); patient SD in C1, slice SD in C2/C3',
                             'C2': 'All slices; empty/empty Dice and IoU = 1',
                             'C3': 'GT-positive slices only', 'C4': 'Pooled voxel counts',
                             'units': 'Fractions in CSV/JSON; percent in the report',
                             'miou': 'Arithmetic mean of liver IoU and background IoU'})


def evaluate(manifest, cfg, out, cache='reports/cache', workers=6, backend='opencv'):
    start = time.perf_counter()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tasks = [(str(cache), m, cfg, backend) for m in manifest]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(evaluate_patient, tasks))
    pp = pd.DataFrame([r[0] for r in results])
    ps = pd.DataFrame([s for r in results for s in r[1]])
    pp.to_csv(out / 'per_patient.csv', index=False, float_format='%.12g')
    ps.to_csv(out / 'per_slice.csv', index=False, float_format='%.12g')
    summary = aggregate(pp, ps)
    write_json(out / 'summary.json', summary)
    write_json(out / 'source_fingerprints.json', {m['patient']:m['source_sha256'] for m in manifest})
    (out / 'config.yaml').write_text(yaml.safe_dump(dict(pipeline=cfg, backend=backend), sort_keys=True))
    write_json(out / 'runtime.json', dict(seconds=time.perf_counter()-start, versions=versions(), workers=workers))
    print(f'{out}: Dice={pp.dice.mean():.6f}, {len(pp)} patients, {len(ps)} slices', flush=True)
    return pp, ps, summary


def main():
    parser = argparse.ArgumentParser(description='Run the fixed HU-based paper method on every labelled CT patient.')
    parser.add_argument('--config', default='configs/paper_protocol.yaml')
    parser.add_argument('--data', default=None)
    parser.add_argument('--out', default=None)
    parser.add_argument('--reports', default='reports')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--backend', choices=['scipy', 'opencv'], default='opencv')
    parser.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    reports = Path(args.reports)
    if args.audit or args.data is not None or not (reports / 'dataset_manifest.json').exists():
        audit(args.data or cfg.get('data', DEFAULT_DATA), reports)
    manifest = json.loads((reports / 'dataset_manifest.json').read_text())
    if any(not (reports / 'cache' / f'{m["patient"]}_{kind}.npy').exists()
           for m in manifest for kind in ('hu', 'gt')):
        # A Git clone includes compact results, but local arrays must be rebuilt.
        manifest = audit(args.data or cfg.get('data', DEFAULT_DATA), reports)
    evaluate(manifest, cfg['pipeline'], args.out or reports / 'paper_protocol',
             reports / 'cache', args.workers, args.backend)


if __name__ == '__main__':
    main()
