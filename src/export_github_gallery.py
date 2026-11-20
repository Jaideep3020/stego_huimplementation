"""Create the compact, repository-ready visualization gallery."""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd


def copy_file(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def selected_cases(table, count=15):
    table = table.sort_values(['dice', 'patient']).reset_index(drop=True)
    indices = np.rint(np.linspace(0, len(table) - 1, count)).astype(int)
    return table.iloc[indices].copy(), table


def write_readme(output, selected):
    lines = [
        '# CHAOS CT Visualization Gallery',
        '',
        f'**{len(selected)} example patients · 20-patient evaluation · 2,874 slices**',
        '',
        'Open this page in GitHub to browse the overlays inline. Each image compares CT, ground truth, prediction, aligned contours, and pixel-wise errors.',
        '',
        '## Jump to a patient',
        '',
        '| Patient | Dice | Liver IoU | Background IoU | mIoU | Overlay |',
        '|---:|---:|---:|---:|---:|---|',
    ]
    for row in selected.itertuples(index=False):
        image = f'CT_{row.patient}_comparison.png'
        lines.append(
            f'| {row.patient} | {100*row.dice:.2f}% | {100*row.iou_liver:.2f}% | '
            f'{100*row.iou_bg:.2f}% | {100*row.miou:.2f}% | [View image](cases/{image}) |'
        )
    lines += [
        '',
        '## Overlays',
        '',
        'Green marks correctly predicted liver, red marks false positives, and blue marks missed liver. In the contour panel, yellow marks coincident ground-truth and prediction boundaries. Display window: −100 to 300 HU. These are display images; scoring uses the original CT values.',
    ]
    for row in selected.itertuples(index=False):
        image = f'CT_{row.patient}_comparison.png'
        lines += [
            '',
            f'### Patient {row.patient} · Dice {100*row.dice:.2f}% · mIoU {100*row.miou:.2f}%',
            '',
            f'![Patient {row.patient}: CT, ground truth, prediction, contours, and errors](cases/{image})',
        ]
    lines += [
        '',
        '## Full evaluation tables',
        '',
        '- [Per-patient evaluation matrix](per_patient.csv): 20 patients, whole-volume counts and metrics.',
        '- [Per-slice evaluation matrix](per_slice.csv): all 2,874 slices.',
        '- [Summary and aggregation definitions](summary.json): patient mean, slice mean, pooled scores and conventions.',
        '- [Original curated bundle guide](../visualization/github/README.md): selection method, full artifact inventory, dataset attribution and license notes.',
        '',
        'Examples are selected at evenly spaced ranks after sorting the cohort by whole-volume Dice. The gallery shows examples across the measured range; evaluation includes all 20 patients.',
        '',
    ]
    (output / 'README.md').write_text('\n'.join(lines))


def run(reports='reports', visualization='visualization', github='visualization/github', gallery='visualization_gallery'):
    reports, visualization = Path(reports), Path(visualization)
    github, gallery = Path(github), Path(gallery)
    table = pd.read_csv(reports / 'paper_protocol/per_patient.csv', dtype={'patient': str})
    selected, ranked = selected_cases(table)
    for output in (github, gallery):
        (output / 'cases').mkdir(parents=True, exist_ok=True)
        for existing in (output / 'cases').glob('*'):
            if existing.is_dir():
                shutil.rmtree(existing)
            else:
                existing.unlink()
    selection = []
    for rank, row in ranked.iterrows():
        if row.patient not in set(selected.patient):
            continue
        case = f'CT_{row.patient}'
        source = visualization / case
        github_case = github / 'cases' / case
        github_case.mkdir()
        copy_file(visualization / 'comparisons' / f'{case}.png', github_case / 'comparison.png')
        copy_file(source / 'mask_volume.npz', github_case / 'predicted_mask_volume.npz')
        metrics = {key: (int(row[key]) if key in ('slices', 'tp', 'fp', 'fn', 'tn') else float(row[key]))
                   for key in ('patient', 'slices', 'tp', 'fp', 'fn', 'tn', 'dice', 'miou', 'iou_liver', 'iou_bg')}
        metrics['patient'] = str(row.patient)
        (github_case / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
        copy_file(visualization / 'comparisons' / f'{case}.png', gallery / 'cases' / f'{case}_comparison.png')
        selection.append(dict(patient=str(row.patient), dice=float(row.dice), miou=float(row.miou),
                              dice_rank_1_low_20_high=int(rank + 1)))
    for output in (github / 'evaluation', gallery):
        output.mkdir(parents=True, exist_ok=True)
        for name in ('per_patient.csv', 'per_slice.csv', 'summary.json'):
            copy_file(reports / 'paper_protocol' / name, output / name)
    copy_file(reports / 'paper_protocol/config.yaml', github / 'evaluation' / 'config.yaml')
    (github / 'selection.json').write_text(json.dumps(dict(
        selection_method='15 evenly spaced ranks from all 20 patients sorted by patient-volume Dice; includes lower and upper extremes',
        selected_cases=selection,
    ), indent=2) + '\n')
    (github / 'README.md').write_text(
        '# Repository visualization and evaluation artifacts\n\n'
        'This folder contains 15 demonstrative CHAOS CT cases, alongside evaluation output for all 20 analysed patients and 2,874 slices. '
        'The selection only limits the visualization examples; it does not limit the evaluation tables.\n\n'
        'Open `../visualization_gallery/README.md` for the inline GitHub gallery. The `cases` folders retain each selected case comparison, metrics, and predicted mask volume. '
        'The `evaluation` folder holds the complete per-patient and per-slice matrices, configuration, and summary.\n'
    )
    write_readme(gallery, selected)
    print(f'Created GitHub gallery: {len(selected)} cases from {len(table)} patients')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reports', default='reports')
    parser.add_argument('--visualization', default='visualization')
    parser.add_argument('--github', default='visualization/github')
    parser.add_argument('--gallery', default='visualization_gallery')
    run(**vars(parser.parse_args()))
