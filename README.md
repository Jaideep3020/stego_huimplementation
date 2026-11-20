# HU-Based Liver Segmentation on CHAOS CT

[![Tests](https://github.com/Jaideep3020/stego_huimplementation/actions/workflows/tests.yml/badge.svg)](https://github.com/Jaideep3020/stego_huimplementation/actions/workflows/tests.yml)

This repository implements and evaluates a fixed Hounsfield Unit (HU) threshold pipeline for liver segmentation on the labelled CHAOS CT training-set cohort. It is an independent implementation informed by Bhusnurmath and Betageri, [*Hounsfield Unit Based Multi-Threshold Approach for Liver Segmentation*](https://doi.org/10.1016/j.procs.2025.04.635), Procedia Computer Science 258 (2025), 3804–3813.

The repository contains source code, the complete evaluation matrix for 20 patients and 2,874 slices, and an inline GitHub gallery of 15 representative patient overlays. It does not distribute original DICOM images or reference masks.

## Start here

- **[Visualization gallery](visualization_gallery/README.md):** 15 inline CT/ground-truth/prediction/overlay/error comparisons.
- **[Complete patient metrics](visualization/github/evaluation/per_patient.csv):** 20 whole-volume results and TP/FP/FN/TN counts.
- **[Complete slice metrics](visualization/github/evaluation/per_slice.csv):** all 2,874 measured slices.
- **[Results analysis](docs/RESULTS_ANALYSIS.md):** distribution, failure cases, aggregation conventions, and limitations.
- **[Evaluation summary](visualization/github/evaluation/summary.json):** patient mean, slice mean, pooled metrics, and definitions.

## Paper context and repository scope

The paper describes HU-based thresholding and morphology as a lightweight approach to liver segmentation. Some implementation details are not fully specified, including exact morphology settings, border handling, connected-component behavior, and metric aggregation. This repository records its choices in [`configs/paper_protocol.yaml`](configs/paper_protocol.yaml), [`docs/PAPER_IMPLEMENTATION_MAP.md`](docs/PAPER_IMPLEMENTATION_MAP.md), and [`docs/REPRODUCTION_GAPS.md`](docs/REPRODUCTION_GAPS.md).

This implementation is a research reproduction and evaluation artifact. It is not author code, a clinical tool, or a claim of clinical validation. MRI is excluded. The separate CHAOS test download is not evaluated here; all reported scores use the labelled CT training-set cohort.

## Current pipeline

The current fixed configuration is:

```yaml
HU range:          40 to 180, inclusive
Median filtering:  disabled
Opening:           disabled
Largest component: 8-connected, per slice
Closing:           7×7 disk
Processing:        independent 2D slices
```

```text
Raw CT DICOM pixel values
        ↓ RescaleSlope / RescaleIntercept
Hounsfield Unit image
        ↓ inclusive 40–180 HU threshold
Binary candidate mask
        ↓ largest 8-connected component
Dominant liver-region candidate
        ↓ 7×7 disk closing
Predicted liver mask
```

Every patient uses these exact settings. There is no learned model, parameter sweep, case-specific tuning, 3D post-processing, or manual correction of masks.

## Results

The headline calculation scores each patient’s complete volume, then averages the 20 patient scores equally. Values below are percentages. Standard deviations use the sample convention (`ddof=1`).

| Metric | Equal-patient mean | Sample SD | Median | Range |
|---|---:|---:|---:|---:|
| Dice | **56.92%** | 17.69 points | 58.49% | 4.10%–82.58% |
| Liver IoU | **41.64%** | 16.04 points | 41.36% | 2.09%–70.32% |
| Background IoU | **89.31%** | 5.97 points | 90.30% | 75.00%–97.68% |
| Two-class mIoU | **65.47%** | 10.79 points | 65.60% | 38.54%–84.00% |

The pooled-voxel result is different because larger scans receive more weight: Dice 53.94%, liver IoU 36.93%, background IoU 89.65%, and mIoU 63.29%. Use one aggregation convention consistently when comparing results.

### Complete patient-level evaluation

| Patient | Slices | Dice | Liver IoU | Background IoU | mIoU |
|---:|---:|---:|---:|---:|---:|
| 1 | 96 | 62.51% | 45.47% | 90.45% | 67.96% |
| 2 | 81 | 82.58% | 70.32% | 97.68% | 84.00% |
| 5 | 95 | 79.17% | 65.52% | 95.31% | 80.42% |
| 6 | 88 | 60.54% | 43.41% | 84.54% | 63.97% |
| 8 | 123 | 54.44% | 37.40% | 90.15% | 63.77% |
| 10 | 110 | 74.56% | 59.44% | 94.94% | 77.19% |
| 14 | 95 | 4.10% | 2.09% | 75.00% | 38.54% |
| 16 | 91 | 50.61% | 33.87% | 84.89% | 59.38% |
| 18 | 111 | 71.07% | 55.13% | 93.23% | 74.18% |
| 19 | 90 | 49.86% | 33.20% | 81.92% | 57.56% |
| 21 | 257 | 67.04% | 50.42% | 95.05% | 72.74% |
| 22 | 101 | 68.81% | 52.45% | 94.43% | 73.44% |
| 23 | 240 | 42.44% | 26.93% | 84.27% | 55.60% |
| 24 | 123 | 40.91% | 25.72% | 81.78% | 53.75% |
| 25 | 235 | 69.70% | 53.49% | 94.36% | 73.93% |
| 26 | 114 | 61.44% | 44.34% | 91.79% | 68.07% |
| 27 | 242 | 48.63% | 32.13% | 87.44% | 59.78% |
| 28 | 102 | 56.37% | 39.25% | 89.50% | 64.37% |
| 29 | 214 | 37.21% | 22.86% | 85.13% | 53.99% |
| 30 | 266 | 56.44% | 39.32% | 94.34% | 66.83% |
| **Mean over 20 patients** | **2,874** | **56.92%** | **41.64%** | **89.31%** | **65.47%** |

## How metrics are calculated

| Metric | Formula | Meaning |
|---|---|---|
| Dice | `2TP / (2TP + FP + FN)` | Liver-mask overlap. |
| Liver IoU | `TP / (TP + FP + FN)` | Intersection over union for liver pixels. |
| Background IoU | `TN / (TN + FP + FN)` | Intersection over union for non-liver pixels. |
| mIoU | `(liver IoU + background IoU) / 2` | Equal average of the two class IoUs. |

CSV and JSON metrics are stored as fractions; the README and gallery show percentages. Empty/empty class scores are set to zero in the current evaluation configuration.

## Visualizations

Open the **[visualization gallery](visualization_gallery/README.md)** on GitHub. It embeds 15 cases selected at evenly spaced ranks after sorting all 20 patients by whole-volume Dice. It therefore includes low-, middle-, and high-performing examples rather than only favorable cases.

Each comparison figure contains five representative liver-positive slices. Columns are:

1. CT image, displayed with a −100 to 300 HU window.
2. Ground-truth liver mask.
3. Predicted liver mask.
4. Boundary overlay: green is reference, red is prediction, yellow is overlapping boundaries.
5. Error map: green is correct liver, red is false positive, blue is missed liver.

The display window affects only the image presentation; it does not change the segmentation calculation. Each selected case also has a whole-volume prediction archive and a JSON metrics file under [`visualization/github/cases`](visualization/github/cases/).

## Results analysis

Performance varies widely between cases, from 4.10% Dice for CT 14 to 82.58% for CT 2. Ten of 20 patients have Dice below 60%, while one has Dice at or above 80%. Background IoU remains substantially higher than liver IoU across the cohort, showing that the threshold rule is better at recognizing non-liver pixels than isolating the liver.

False positives are a recurring error pattern in lower-performing cases. This is expected for a fixed HU interval because other abdominal tissues can have similar attenuation values. The gallery makes these errors inspectable case by case. See the [full analysis](docs/RESULTS_ANALYSIS.md) for the evidence and limits of interpretation.

## Repository structure

```text
configs/
  paper_protocol.yaml          Current fixed HU pipeline settings
  alignment_overrides.yaml     Recorded image/mask alignment decisions
src/
  io_chaos.py                  DICOM audit, HU conversion, data loading
  pipeline.py                  Slice segmentation stages
  metrics.py                   Confusion counts, Dice, IoU, mIoU
  run_experiment.py            Cohort evaluation and CSV/JSON results
  export_segmentations.py      Full local masks and comparison figures
  export_github_gallery.py     Compact GitHub gallery export
  report.py                    Markdown report generation
  check_integrity.py           Fresh-source prediction and consistency check
  verify.py                    Repeat-evaluation comparison
reports/
  paper_protocol/              Current full metrics and configuration
  REPRODUCTION_REPORT.md       Detailed method and results report
visualization/
  github/                      Repository-ready metrics and selected cases
visualization_gallery/
  README.md                    Inline GitHub gallery entry point
DATASET/
  CHAOS_Train_Sets/            Local source data; ignored by Git
tests/                         Unit and integration tests
```

## Setup and reproduction

Clone the repository and create an environment:

```sh
git clone https://github.com/Jaideep3020/stego_huimplementation.git
cd stego_huimplementation
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Place the labelled CHAOS CT training data at:

```text
DATASET/CHAOS_Train_Sets/Train_Sets/CT
```

Run the complete workflow:

```sh
python run.py all --workers 6
```

Or run individual stages:

```sh
python run.py audit --workers 6
python run.py evaluate --workers 6
python run.py report
python run.py visualization --workers 6
python -m src.export_github_gallery
python run.py integrity --workers 6
python run.py verify --workers 6
python run.py test
```

`make all WORKERS=6` and `make github-gallery` provide equivalent Make targets. The full local visualization export is ignored by Git; the compact gallery in `visualization/github/` and `visualization_gallery/` is intended for repository browsing.

## Verification and limitations

The project can compare saved results with a fresh source-data prediction and repeat the evaluation deterministically. See `reports/integrity_check.json` and `reports/verification.json` after running the checks.

The results depend on the labelled CHAOS CT cohort, the fixed preprocessing choices, and 2D processing. They should not be generalized to other scanners, acquisition protocols, pathologies, or clinical decision-making without separate validation.

## Dataset and paper attribution

CHAOS dataset: Kavur et al., [*CHAOS – Combined (CT-MR) Healthy Abdominal Organ Segmentation Challenge Data*](https://doi.org/10.5281/zenodo.3431873), distributed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Paper: Rohini A. Bhusnurmath and Shivaleela Betageri, [*Hounsfield Unit Based Multi-Threshold Approach for Liver Segmentation*](https://doi.org/10.1016/j.procs.2025.04.635), Procedia Computer Science 258 (2025), 3804–3813.

Source DICOM series and reference masks are not redistributed in this repository. Dataset-derived visualization artifacts remain subject to the CHAOS license.
