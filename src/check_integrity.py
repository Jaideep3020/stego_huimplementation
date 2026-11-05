"""Recalculate IoU from original CT/GT files, without using prediction/filter caches."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import pydicom
import yaml

from .pipeline import segment_slice


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_patient(task):
    """Decode original files, check caches, and independently count the fixed paper method."""
    meta, configs, reports = task
    pid = meta['patient']
    reports = Path(reports)
    hu_cache = np.load(reports / f'cache/{pid}_hu.npy', mmap_mode='r')
    gt_cache = np.load(reports / f'cache/{pid}_gt.npy', mmap_mode='r')
    rows = {name: [] for name in configs}
    digest = hashlib.sha256()
    for index, (dcm_path, gt_path) in enumerate(zip(meta['dicom_files'], meta['gt_files'])):
        raw_dcm, raw_gt = Path(dcm_path).read_bytes(), Path(gt_path).read_bytes()
        digest.update(raw_dcm)
        digest.update(raw_gt)
        ds = pydicom.dcmread(io.BytesIO(raw_dcm))
        require(ds.Modality == 'CT', f'{pid}: non-CT input')
        hu = ds.pixel_array.astype(np.float32) * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
        labels = np.asarray(Image.open(io.BytesIO(raw_gt)))
        require(set(np.unique(labels)) <= {0, 1, 255}, f'{pid}: unexpected mask labels')
        gt = labels > 0
        require(np.array_equal(hu, hu_cache[index]), f'{pid}/{index}: HU cache differs from source')
        require(np.array_equal(gt, gt_cache[index]), f'{pid}/{index}: GT cache differs from source')
        for name, cfg in configs.items():
            # Reference SciPy backend and fresh median filtering, not accelerated caches.
            prediction = segment_slice(hu, **cfg, backend='scipy')
            tp = int(np.count_nonzero(prediction & gt))
            fp = int(np.count_nonzero(prediction & ~gt))
            fn = int(np.count_nonzero(~prediction & gt))
            tn = int(np.count_nonzero(~prediction & ~gt))
            rows[name].append((index, tp, fp, fn, tn))
    require(digest.hexdigest() == meta['source_sha256'], f'{pid}: source fingerprint changed')
    return pid, rows


def check(reports='reports', workers=6):
    reports = Path(reports)
    manifest = json.loads((reports / 'dataset_manifest.json').read_text())
    configs = {'paper_protocol': yaml.safe_load((reports / 'paper_protocol/config.yaml').read_text())['pipeline']}
    tasks = [(m, {name: cfg for name, cfg in configs.items()}, str(reports)) for m in manifest]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        raw = list(pool.map(check_patient, tasks))
    result = dict(source_sha256_verified=True, hu_and_gt_caches_match_originals=True,
                  reference_backend='scipy; original DICOM and GT; fresh per-slice median filtering',
                  scope='Original-source fingerprints, source/cache equality, TP/FP/FN/TN, and C1 Dice/IoU/mIoU for the fixed paper method. Anatomical label correctness requires separate visual review.',
                  patients=len(manifest), slices=sum(m['slices'] for m in manifest), protocols={})
    for protocol in configs:
        ps = pd.read_csv(reports / protocol / 'per_slice.csv', dtype={'patient': str})
        pp = pd.read_csv(reports / protocol / 'per_patient.csv', dtype={'patient': str}).set_index('patient')
        summary = json.loads((reports / protocol / 'summary.json').read_text())
        expected_keys = {(m['patient'], i) for m in manifest for i in range(m['slices'])}
        actual_keys = list(zip(ps.patient, ps['slice']))
        require(len(actual_keys) == len(set(actual_keys)) and set(actual_keys) == expected_keys, f'{protocol}: missing/duplicate slices')
        require(set(pp.index) == {m['patient'] for m in manifest} and len(pp) == len(manifest), f'{protocol}: patient coverage mismatch')
        ps = ps.set_index(['patient', 'slice'])
        scores = []
        for pid, protocols in raw:
            counts = np.asarray(protocols[protocol], dtype=np.int64)
            expected = ps.loc[[(pid, int(i)) for i in counts[:, 0]], ['tp', 'fp', 'fn', 'tn']].to_numpy()
            require(np.array_equal(counts[:, 1:], expected), f'{protocol}/{pid}: saved confusion counts differ from raw-data prediction')
            totals = counts[:, 1:].sum(axis=0)
            require(np.array_equal(totals, pp.loc[pid, ['tp', 'fp', 'fn', 'tn']].to_numpy()), f'{protocol}/{pid}: patient totals differ')
            tp, fp, fn, tn = map(int, totals)
            liver = tp / (tp + fp + fn) if tp + fp + fn else 1.0
            background = tn / (tn + fp + fn) if tn + fp + fn else 1.0
            miou = (liver + background) / 2
            require(np.isclose(pp.loc[pid, 'iou_liver'], liver, atol=1e-10, rtol=0), f'{protocol}/{pid}: liver IoU differs')
            require(np.isclose(pp.loc[pid, 'miou'], miou, atol=1e-10, rtol=0), f'{protocol}/{pid}: mIoU differs')
            dice = 2*tp / (2*tp+fp+fn) if 2*tp+fp+fn else 1.0
            require(np.isclose(pp.loc[pid, 'dice'], dice, atol=1e-10, rtol=0), f'{protocol}/{pid}: Dice differs')
            scores.append((liver, miou, dice))
        values = np.asarray(scores)
        for col, metric in enumerate(['iou_liver', 'miou', 'dice']):
            require(np.isclose(values[:, col].mean(), summary['C1'][metric]['mean'], atol=1e-12, rtol=0), f'{protocol}: mean {metric} differs')
            require(np.isclose(values[:, col].std(), summary['C1'][metric]['std'], atol=1e-12, rtol=0), f'{protocol}: SD {metric} differs')
        result['protocols'][protocol] = dict(confusion_counts_match=True, mean_liver_iou=float(values[:, 0].mean()), mean_iou=float(values[:, 1].mean()), mean_dice=float(values[:, 2].mean()))
    (reports / 'integrity_check.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reports', default='reports')
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    check(args.reports, args.workers)
