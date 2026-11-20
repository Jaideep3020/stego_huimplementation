# HU-only segmentation adaptation: Dice and mIoU

All **20 labelled CT patients and 2874 slices** are included.

| Metric | Patient mean % | Patient SD (percentage points) |
|---|---:|---:|
| Dice | 56.9213 | 17.6908 |
| mIoU (liver + background) | 65.4740 | 10.7905 |

Each patient is scored over its complete volume, then patient scores are averaged equally. SD uses ddof=1 (sample SD). CSV/JSON values are fractions; this report uses percent.

**Dice** = 2TP/(2TP+FP+FN). **mIoU** = [TP/(TP+FP+FN) + TN/(TN+FP+FN)]/2. Empty/empty class scores are 0. Liver/background IoU components and confusion counts are retained in the CSVs to audit mIoU.

## Method: HU-Only Adaptation Borrowing P1 Parameters

> **Note**: This is an HU-only adaptation borrowing selected morphological and threshold parameters from P1—it is **not** an equivalent implementation of P1.

> P1 predicts clusters from learned BiomedCLIP embeddings, selects a liver cluster via N2 naming, and refines probability maps using guided filtering. In contrast, this pipeline operates strictly via direct HU intensity thresholding.

> Crucially, the pixel-wise use of [40, 180] HU is a new adaptation and has **not** been validated by the P1 results (which use 40–180 HU only for candidate cluster mean intensity).

**Pipeline Order:**

Raw CT DICOM → HU conversion → pixel threshold [40, 180] HU → largest 2D eight-connected component → disk-radius-3 binary closing (7×7 footprint).

- Median filtering is disabled (`med_k=0`).

- Opening of the liver mask is disabled (`open_k=0`).

- Structuring element: `disk`, closing footprint radius 3 (`close_k=7`).

- CT visualization window: [−150, 250] HU (segmentation thresholds are applied directly to raw HU).

```yaml
close_k: 7
connectivity: 2
med_k: 0
open_k: 0
order: fig3
shape: disk
tmax: 180
tmin: 40
use_lcc: true
```

## Per-patient results

| Patient | Slices | Dice % | mIoU % |
|---|---:|---:|---:|
| 1 | 96 | 62.5130 | 67.9577 |
| 2 | 81 | 82.5754 | 84.0028 |
| 5 | 95 | 79.1697 | 80.4156 |
| 6 | 88 | 60.5403 | 63.9739 |
| 8 | 123 | 54.4402 | 63.7749 |
| 10 | 110 | 74.5583 | 77.1896 |
| 14 | 95 | 4.0999 | 38.5446 |
| 16 | 91 | 50.6060 | 59.3844 |
| 18 | 111 | 71.0741 | 74.1791 |
| 19 | 90 | 49.8553 | 57.5648 |
| 21 | 257 | 67.0418 | 72.7371 |
| 22 | 101 | 68.8104 | 73.4381 |
| 23 | 240 | 42.4374 | 55.6016 |
| 24 | 123 | 40.9118 | 53.7467 |
| 25 | 235 | 69.6982 | 73.9263 |
| 26 | 114 | 61.4414 | 68.0656 |
| 27 | 242 | 48.6303 | 59.7830 |
| 28 | 102 | 56.3712 | 64.3740 |
| 29 | 214 | 37.2091 | 53.9950 |
| 30 | 266 | 56.4424 | 66.8263 |

## Dataset and alignment

Source: the local labelled CHAOS CT directory. MRI is excluded. Actual slice counts are 81–266 per patient. Every source DICOM/GT filename, source SHA256 and alignment decision is recorded in dataset_manifest.json.

All final mask orderings are forward. configs/alignment_overrides.yaml preserves forward order based on visual anatomy.

## Visualization

visualization/CT_<patient>/ contains predicted masks, matched GT, segmented CT display images and compressed boolean volumes. visualization/comparisons/ contains five slices per patient. visualization/preview.png shows the lower-median Dice patient on its largest-GT-area slice. Titles report whole-patient scores.

Original CT display window: −150 to 250 HU. Overlay: green correct liver, red false positive, blue false negative. These display settings do not affect the algorithm.

Generated preview: `visualization/preview.png` (created locally by the visualization command).

The six-stage figure is reports/figures/fig3_replica.png. Dataset HU histogram: reports/dataset_visualization/hu_histogram.png.

## Verification

Repeated fixed-method per-patient CSV, per-slice CSV and summary JSON are byte-identical. See verification.json.
Original-source fingerprints, source/cache equality and independently counted Dice/IoU match the saved results. See integrity_check.json.

Run `python run.py all` to reproduce the audit, tests, fixed evaluation, visualizations, checks and report.

```json
{
  "python": "3.14.5",
  "opencv_runtime": "5.1.0",
  "numpy": "2.5.2",
  "scipy": "1.18.1",
  "scikit-image": "0.26.0",
  "pydicom": "3.0.2",
  "pandas": "3.0.5",
  "matplotlib": "3.11.1",
  "pyyaml": "6.0.3",
  "Pillow": "12.3.0",
  "opencv-python-headless": "5.0.0.93"
}
```
