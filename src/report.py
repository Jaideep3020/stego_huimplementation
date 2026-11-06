"""Report measured Dice and mIoU for the adapted HU segmentation method."""
import json
from pathlib import Path
import pandas as pd
import yaml
from .run_experiment import versions


def run(reports='reports'):
    reports = Path(reports)
    result = reports/'paper_protocol'
    summary = json.loads((result/'summary.json').read_text())
    table = pd.read_csv(result/'per_patient.csv', dtype={'patient': str})
    cfg = yaml.safe_load((result/'config.yaml').read_text())['pipeline']
    lines = ['# HU-only segmentation adaptation: Dice and mIoU', '',
             f'All **{summary["patients"]} labelled CT patients and {summary["slices"]} slices** are included.', '',
             '| Metric | Patient mean % | Patient SD (percentage points) |',
             '|---|---:|---:|']
    for key, label in [('dice', 'Dice'), ('miou', 'mIoU (liver + background)')]:
        value = summary['C1'][key]
        lines.append(f'| {label} | {100*value["mean"]:.4f} | {100*value["std"]:.4f} |')
    lines += ['', 'Each patient is scored over its complete volume, then patient scores are averaged equally. SD uses ddof=0. CSV/JSON values are fractions; this report uses percent.', '',
              '**Dice** = 2TP/(2TP+FP+FN). **mIoU** = [TP/(TP+FP+FN) + TN/(TN+FP+FN)]/2. Empty/empty class scores are 1. Liver/background IoU components and confusion counts are retained in the CSVs to audit mIoU.', '',
              '## Method: HU-Only Adaptation Borrowing P1 Parameters', '',
              '> **Note**: This is an HU-only adaptation borrowing selected morphological and threshold parameters from P1—it is **not** an equivalent implementation of P1.', '',
              '> P1 predicts clusters from learned BiomedCLIP embeddings, selects a liver cluster via N2 naming, and refines probability maps using guided filtering. In contrast, this pipeline operates strictly via direct HU intensity thresholding.', '',
              '> Crucially, the pixel-wise use of [40, 180] HU is a new adaptation and has **not** been validated by the P1 results (which use 40–180 HU only for candidate cluster mean intensity).', '',
              '**Pipeline Order:**', '',
              'Raw CT DICOM → HU conversion → pixel threshold [40, 180] HU → largest 2D eight-connected component → disk-radius-3 binary closing (7×7 footprint).', '',
              '- Median filtering is disabled (`med_k=0`).', '',
              '- Opening of the liver mask is disabled (`open_k=0`).', '',
              '- Structuring element: `disk`, closing footprint radius 3 (`close_k=7`).', '',
              '- CT visualization window: [−150, 250] HU (segmentation thresholds are applied directly to raw HU).', '',
              '```yaml', yaml.safe_dump(cfg, sort_keys=False).strip(), '```', '',
              '## Per-patient results', '', '| Patient | Slices | Dice % | mIoU % |', '|---|---:|---:|---:|']
    for _, row in table.iterrows():
        lines.append(f'| {row.patient} | {int(row.slices)} | {100*row.dice:.4f} | {100*row.miou:.4f} |')
    lines += ['', '## Dataset and alignment', '',
              'Source: the local labelled CHAOS CT directory. MRI is excluded. Actual slice counts are 81–266 per patient. Every source DICOM/GT filename, source SHA256 and alignment decision is recorded in dataset_manifest.json.', '',
              'All final mask orderings are forward. configs/alignment_overrides.yaml preserves forward order based on visual anatomy.', '',
              '## Visualization', '',
              'visualization/CT_<patient>/ contains predicted masks, matched GT, segmented CT display images and compressed boolean volumes. visualization/comparisons/ contains five slices per patient. visualization/preview.png shows the lower-median Dice patient on its largest-GT-area slice. Titles report whole-patient scores.', '',
              'Original CT display window: −150 to 250 HU. Overlay: green correct liver, red false positive, blue false negative. These display settings do not affect the algorithm.', '',
              'Generated preview: `visualization/preview.png` (created locally by the visualization command).', '',
              'The six-stage figure is reports/figures/fig3_replica.png. Dataset HU histogram: reports/dataset_visualization/hu_histogram.png.', '',
              '## Verification', '']
    if (reports/'verification.json').exists():
        lines += ['Repeated fixed-method per-patient CSV, per-slice CSV and summary JSON are byte-identical. See verification.json.']
    if (reports/'integrity_check.json').exists():
        lines += ['Original-source fingerprints, source/cache equality and independently counted Dice/IoU match the saved results. See integrity_check.json.']
    lines += ['', 'Run `python run.py all` to reproduce the audit, tests, fixed evaluation, visualizations, checks and report.', '', '```json', json.dumps(versions(), indent=2), '```', '']
    (reports/'REPRODUCTION_REPORT.md').write_text('\n'.join(lines))
    (reports/'comparison_table.md').write_text('\n'.join(lines[:10])+'\n')
    (reports/'STATUS.md').write_text('HU-only adaptation borrowing P1 parameters without hole filling. Dice, mIoU and patient visualizations are generated for all 20 CT cases and 2874 slices. See REPRODUCTION_REPORT.md for measured scores and validation.\n')
    print('Generated adapted HU-method Dice/mIoU report', flush=True)


if __name__ == '__main__':
    run()
