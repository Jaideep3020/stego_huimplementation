# Paper-method liver segmentation: Dice and mIoU

All **20 labelled CT patients and 2874 slices** are included.

| Metric | Patient mean % | Patient SD (percentage points) |
|---|---:|---:|
| Dice | 71.2483 | 19.1673 |
| mIoU (liver + background) | 76.2387 | 11.9060 |

Each patient is scored over its complete volume, then patient scores are averaged equally. SD uses ddof=0. CSV/JSON values are fractions; this report uses percent.

**Dice** = 2TP/(2TP+FP+FN). **mIoU** = [TP/(TP+FP+FN) + TN/(TN+FP+FN)]/2. Empty/empty class scores are 1. Liver/background IoU components and confusion counts are retained in the CSVs to audit mIoU.

## Method

Raw CT DICOM → HU conversion → 3×3 median filter → inclusive 50–200 HU threshold → 5×5 disk opening → largest 2D component (8-connectivity) → 5×5 disk closing.

This follows the order described in Section 4.2 of the [paper](https://doi.org/10.1016/j.procs.2025.04.635). It processes each slice independently. Every patient uses the same fixed parameters; there is no parameter tuning.

```yaml
close_k: 5
connectivity: 2
med_k: 3
open_k: 5
order: fig3
shape: disk
tmax: 200
tmin: 50
use_lcc: true
```

The paper omits kernel sizes, discrete footprint, borders, connectivity and aggregation. Its Section 3 description also differs in operation ordering. Those choices are documented in docs/REPRODUCTION_GAPS.md and docs/PAPER_VERIFICATION.md; exact author-code equivalence is not established. mIoU is an additional requested metric; the paper does not report it.

## Per-patient results

| Patient | Slices | Dice % | mIoU % |
|---|---:|---:|---:|
| 1 | 96 | 87.9999 | 88.1145 |
| 2 | 81 | 92.1625 | 92.2644 |
| 5 | 95 | 90.3681 | 90.2521 |
| 6 | 88 | 70.6137 | 72.3839 |
| 8 | 123 | 74.2828 | 77.5036 |
| 10 | 110 | 88.7168 | 88.8782 |
| 14 | 95 | 6.4553 | 42.7170 |
| 16 | 91 | 65.1203 | 70.1860 |
| 18 | 111 | 87.0425 | 87.2355 |
| 19 | 90 | 58.8557 | 64.4356 |
| 21 | 257 | 81.4910 | 83.2435 |
| 22 | 101 | 83.3285 | 84.4517 |
| 23 | 240 | 61.2682 | 68.5809 |
| 24 | 123 | 49.7255 | 60.1830 |
| 25 | 235 | 80.8744 | 82.4280 |
| 26 | 114 | 79.3703 | 81.1437 |
| 27 | 242 | 68.5963 | 73.3556 |
| 28 | 102 | 72.8356 | 75.9806 |
| 29 | 214 | 53.1726 | 64.4188 |
| 30 | 266 | 72.6849 | 77.0168 |

## Dataset and alignment

Source: the local labelled CHAOS CT directory. MRI is excluded. Actual slice counts are 81–266 per patient; the paper gives different estimates. Every source DICOM/GT filename, source SHA256 and alignment decision is recorded in dataset_manifest.json.

All final mask orderings are forward. A rough-band overlap heuristic incorrectly proposed reversing CT14. configs/alignment_overrides.yaml preserves forward order based on visual anatomy. See figures/alignment_CT_14.png. No predicted masks are manually corrected.

## Visualization

visualization/CT_<patient>/ contains predicted masks, matched GT, segmented CT display images and compressed boolean volumes. visualization/comparisons/ contains five slices per patient. visualization/preview.png shows the lower-median Dice patient on its largest-GT-area slice. Titles report whole-patient scores.

Original CT display window: -100 to 300 HU. Overlay: green correct liver, red false positive, blue false negative. These display settings do not affect the algorithm.

Generated preview: `visualization/preview.png` (created locally by the visualization command).

The six-stage figure is reports/figures/fig3_replica.png. Dataset HU histogram: reports/dataset_visualization/hu_histogram.png.

## Verification

Repeated fixed-method per-patient CSV, per-slice CSV and summary JSON are byte-identical. See verification.json.
Original-source fingerprints, source/cache equality and independently counted Dice/IoU match the saved results. See integrity_check.json.

Run `python run.py all` to reproduce the audit, tests, fixed evaluation, visualizations, checks and report.

```json
{
  "python": "3.14.5",
  "opencv_runtime": "5.0.0",
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
