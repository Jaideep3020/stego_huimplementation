"""Export the fixed paper-method segmentation and patient visualizations."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
from PIL import Image
import yaml

from .pipeline import segment_slice
from .run_experiment import median_volume, write_json


def export_patient(task):
    reports, out, meta = task
    import cv2
    cv2.setNumThreads(1)
    reports, out = Path(reports), Path(out)
    pid = meta['patient']
    hu = np.load(reports / f'cache/{pid}_hu.npy', mmap_mode='r')
    gt = np.load(reports / f'cache/{pid}_gt.npy', mmap_mode='r')
    result = reports / 'paper_protocol'
    cfg = yaml.safe_load((result / 'config.yaml').read_text())['pipeline']
    target = out / f'CT_{pid}'
    for name in ['masks', 'segmented_ct', 'ground_truth']:
        (target / name).mkdir(parents=True, exist_ok=True)
    filtered = median_volume(reports / 'cache', pid, cfg['med_k'])
    saved = pd.read_csv(result / 'per_slice.csv', dtype={'patient': str})
    saved = saved[saved.patient == pid].set_index('slice')
    predicted = np.empty(gt.shape, dtype=bool)
    mapping = []
    for index, (image, ground_truth) in enumerate(zip(filtered, gt)):
        prediction = segment_slice(image, **cfg, backend='opencv', prefiltered=True)
        predicted[index] = prediction
        counts = [np.count_nonzero(prediction & ground_truth), np.count_nonzero(prediction & ~ground_truth),
                  np.count_nonzero(~prediction & ground_truth), np.count_nonzero(~prediction & ~ground_truth)]
        if not np.array_equal(counts, saved.loc[index, ['tp', 'fp', 'fn', 'tn']].to_numpy()):
            raise ValueError(f'CT {pid}/slice {index}: prediction differs from measured result')
        name = f'slice_{index:04d}.png'
        Image.fromarray(prediction.astype(np.uint8)*255).save(target/'masks'/name)
        Image.fromarray(ground_truth.astype(np.uint8)*255).save(target/'ground_truth'/name)
        display = np.rint(np.clip((hu[index]+150)/400, 0, 1)*255).astype(np.uint8)
        display[~prediction] = 0
        Image.fromarray(display).save(target/'segmented_ct'/name)
        if not np.array_equal(np.asarray(Image.open(target/'masks'/name)) == 255, prediction):
            raise ValueError(f'PNG round-trip failed: CT {pid}/{name}')
        mapping.append(dict(slice=index, output_png=name, source_dicom=meta['dicom_files'][index],
                            source_ground_truth=meta['gt_files'][index]))
    np.savez_compressed(target/'mask_volume.npz', mask=predicted)
    with np.load(target/'mask_volume.npz') as archive:
        if not np.array_equal(archive['mask'], predicted):
            raise ValueError(f'Volume round-trip failed: CT {pid}')
    pd.DataFrame(mapping).to_csv(target/'slice_map.csv', index=False)
    write_json(target/'metadata.json', dict(patient=pid, method='paper_protocol', parameters=cfg,
               shape=list(gt.shape), axis_order=['slice', 'row', 'column'],
               mask_png_values={'background': 0, 'predicted_liver': 255},
               segmented_ct_display_window_hu=[-150, 250], segmented_ct_is_display_only=True,
               pixel_spacing_mm=meta['pixel_spacing_mm'], z_spacing_mm=meta['z_spacing_mm'],
               source_sha256=meta['source_sha256'], gt_reversed=meta['gt_reversed'],
               alignment_override=meta.get('alignment_override')))
    print(f'Exported CT {pid}: {len(gt)} paper-method masks; measured counts and saved masks agree', flush=True)
    return pid


def comparison(pid, reports, out, indices=None, filename=None):
    import os
    import tempfile
    os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'liver-hu-matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    hu = np.load(reports/f'cache/{pid}_hu.npy', mmap_mode='r')
    gt = np.load(reports/f'cache/{pid}_gt.npy', mmap_mode='r')
    positive = np.flatnonzero(gt.reshape(len(gt), -1).any(axis=1))
    if indices is None:
        indices = positive[np.rint(np.linspace(0, len(positive)-1, 5)).astype(int)]
    with np.load(out/f'CT_{pid}'/'mask_volume.npz') as archive:
        masks = archive['mask']
    scores = pd.read_csv(reports/'paper_protocol/per_patient.csv', dtype={'patient': str}).set_index('patient').loc[pid]
    fig, axes = plt.subplots(len(indices), 4, figsize=(13, 3*len(indices)), squeeze=False)
    for row, index in enumerate(indices):
        prediction = masks[index]
        for col, image in enumerate([hu[index], gt[index], prediction]):
            axes[row, col].imshow(image, cmap='gray', vmin=-150 if col==0 else 0, vmax=250 if col==0 else 1)
        axes[row, 3].imshow(hu[index], cmap='gray', vmin=-150, vmax=250)
        error = np.zeros((*gt[index].shape, 4))
        error[prediction & gt[index]] = [0, 1, 0, .6]
        error[prediction & ~gt[index]] = [1, 0, 0, .6]
        error[~prediction & gt[index]] = [0, .5, 1, .6]
        axes[row, 3].imshow(error)
        for ax in axes[row]:
            ax.set_xticks([])
            ax.set_yticks([])
        axes[row, 0].set_ylabel(f'Slice {index}')
    titles = ['Original CT', 'Ground truth', 'Paper-method segmentation', 'Errors: TP green / FP red / FN blue']
    for ax, title in zip(axes[0], titles):
        ax.set_title(title, fontsize=10)
    fig.suptitle(f'CT {pid} — patient-volume Dice {100*scores.dice:.2f}% · mIoU {100*scores.miou:.2f}%', fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .96))
    path = filename or out/'comparisons'/f'CT_{pid}.png'
    fig.savefig(path, dpi=125)
    plt.close(fig)
    return path


def run(reports='reports', out='visualization', workers=6, archive=True):
    reports, out = Path(reports), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out/'comparisons').mkdir(exist_ok=True)
    manifest = json.loads((reports/'dataset_manifest.json').read_text())
    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(export_patient, [(str(reports), str(out), meta) for meta in manifest]))
    for meta in manifest:
        comparison(meta['patient'], reports, out)
    table = pd.read_csv(reports/'paper_protocol/per_patient.csv', dtype={'patient': str}).sort_values(['dice', 'patient'])
    pid = table.iloc[(len(table)-1)//2].patient
    gt = np.load(reports/f'cache/{pid}_gt.npy', mmap_mode='r')
    index = int(np.argmax(gt.reshape(len(gt), -1).sum(axis=1)))
    comparison(pid, reports, out, [index], out/'preview.png')
    (out/'scores').mkdir(exist_ok=True)
    for name in ['per_patient.csv', 'per_slice.csv', 'summary.json', 'config.yaml']:
        shutil.copy2(reports/'paper_protocol'/name, out/'scores'/name)
    count = sum(meta['slices'] for meta in manifest)
    for name in ['masks', 'segmented_ct', 'ground_truth']:
        if len(list(out.glob(f'CT_*/{name}/*.png'))) != count:
            raise ValueError(f'Export count mismatch: {name}')
    write_json(out/'export_verification.json', dict(method='paper_protocol', patients=len(manifest), slices=count,
               confusion_counts_match_measured_results=True, png_round_trip=True, npz_round_trip=True,
               preview=dict(patient=pid, slice=index, selection='Lower-median patient Dice; largest GT-area slice')))
    (out/'README.md').write_text('''# Paper-method patient segmentations

One fixed 50–200 HU pipeline is applied to every CT patient.

- CT_<patient>/masks/: predicted 0/255 PNG masks for every slice.
- CT_<patient>/ground_truth/: matched reference masks, 0/255.
- CT_<patient>/segmented_ct/: CT display pixels inside the predicted mask. Display window -150 to 250 HU; these are not quantitative HU images.
- mask_volume.npz: boolean `mask` array indexed [slice, row, column].
- slice_map.csv: original DICOM/GT filenames for every output. metadata.json: parameters, spacing and fingerprint.
- comparisons/: five slices spanning each patient's GT-positive range, showing original CT, GT, prediction and errors.
- Green = correct liver, red = non-liver incorrectly included, blue = missed liver.
- scores/: measured per-patient/per-slice Dice and two-class mIoU, including IoU components and confusion counts.
- preview.png: largest-GT-area slice of the lower-median patient by Dice. Titles show whole-patient scores.

Every exported mask is checked against measured TP/FP/FN/TN. PNG and NPZ files are read back and verified. No manual mask correction is applied.
''')
    if archive:
        path = shutil.make_archive(str(out), 'zip', root_dir=out.parent, base_dir=out.name)
        print(f'Archive ready: {path}', flush=True)
    print(f'Paper-method visualization complete: {out}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reports', default='reports')
    parser.add_argument('--out', default='visualization')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--no-archive', action='store_true')
    args = parser.parse_args()
    run(args.reports, args.out, args.workers, not args.no_archive)
