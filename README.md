# HU-based liver segmentation on CHAOS CT

[![Tests](https://github.com/Jaideep3020/stego_huimplementation/actions/workflows/tests.yml/badge.svg)](https://github.com/Jaideep3020/stego_huimplementation/actions/workflows/tests.yml)

A structured implementation of the HU-based liver segmentation method described by Bhusnurmath & Betageri, *Hounsfield Unit Based Multi-Threshold Approach for Liver Segmentation*, Procedia Computer Science 258 (2025), 3804–3813, [DOI](https://doi.org/10.1016/j.procs.2025.04.635).

The project applies **one fixed paper-method configuration** to all **20 labelled local CT patients and 2,874 slices**. The requested outputs are **Dice, mIoU, and patient segmentation visualizations**. MRI is excluded. Parameters are not tuned.


## Evaluation results

| Metric | Mean over 20 complete patient volumes |
|---|---:|
| Dice | **71.25%** |
| mIoU, liver + background | **76.24%** |

These are measured results from this implementation, not the paper's reported values. Each patient's complete 3D volume is scored first, then the 20 patient scores are averaged equally (population SD). MRI is excluded. The reported mIoU is the mean of liver IoU and background IoU.

**Start here on GitHub:** open the dedicated [visualization gallery](visualization_gallery/README.md). It shows all 15 overlays inline, provides a patient jump table, and links to the complete evaluation matrices. Its files are grouped in one top-level folder for straightforward browsing. The original [curated artifact bundle](visualization/github/README.md) remains available with the complete file inventory and dataset attribution. The broader [reproduction report](reports/REPRODUCTION_REPORT.md) includes patient-level results and method limitations.

Read [the results analysis](docs/RESULTS_ANALYSIS.md) for cohort distribution, low- and high-performing cases, pooled versus equal-patient aggregation, visual-review guidance, and the limits of this fixed HU method.

### How to inspect the evaluation

1. Open `visualization/github/evaluation/summary.json` for cohort means, standard deviations, sample counts, and the definitions of each aggregation.
2. Open `per_patient.csv` to compare the 20 whole-volume patient scores. Each row includes slice count, TP/FP/FN/TN, Dice, liver IoU, background IoU, and mIoU.
3. Open `per_slice.csv` for the corresponding measurements on every one of the 2,874 slices. CSV scores are fractions; multiply by 100 for percentages.
4. For a patient case, open `visualization/github/cases/CT_<id>/comparison.png`. The five rows show representative GT-positive slices; columns show CT, ground truth, prediction, aligned contours, and error overlay. Green marks correct liver, red false positive, blue missed liver, and yellow overlapping contours.
5. The same case folder has `metrics.json` with that patient's full-volume counts and scores and `predicted_mask_volume.npz` with all predicted slices. The NPZ contains predictions only; source DICOMs and ground-truth masks are not included in the curated bundle.

The 15 displayed patients are selected by evenly spaced ranks after sorting all 20 by whole-volume Dice, so the examples span the observed score range. See [the bundle guide](visualization/github/README.md) for the artifact inventory, attribution, and license notes.

### Browse the example visualizations on GitHub

Open the [15-case gallery folder](visualization/github/cases/) in GitHub and select a patient folder, then click `comparison.png` to view the overlay. The image has five representative liver-positive slices. Read each row from left to right: CT image, ground-truth mask, predicted mask, contours, and error map. In the contour panel, green is the reference boundary, red is the predicted boundary, and yellow is where they overlap. In the error panel, green pixels are correctly predicted liver, red pixels are false positives, and blue pixels are missed liver. The CT display window is −100 to 300 HU and affects display only.

The examples are chosen by evenly spaced ranks across patient-volume Dice, not hand-picked visual quality. This includes poor, middle, and strong cases; see [`selection.json`](visualization/github/selection.json) for the exact selected patient IDs and scores. The 15 examples are illustrations; the matrices still cover all 20 patients.

| Patient | Dice | mIoU | Overlay |
|---:|---:|---:|---|
| 14 | 6.46% | 42.72% | [View comparison](visualization/github/cases/CT_14/comparison.png) |
| 24 | 49.73% | 60.18% | [View comparison](visualization/github/cases/CT_24/comparison.png) |
| 19 | 58.86% | 64.44% | [View comparison](visualization/github/cases/CT_19/comparison.png) |
| 23 | 61.27% | 68.58% | [View comparison](visualization/github/cases/CT_23/comparison.png) |
| 16 | 65.12% | 70.19% | [View comparison](visualization/github/cases/CT_16/comparison.png) |
| 6 | 70.61% | 72.38% | [View comparison](visualization/github/cases/CT_6/comparison.png) |
| 30 | 72.68% | 77.02% | [View comparison](visualization/github/cases/CT_30/comparison.png) |
| 8 | 74.28% | 77.50% | [View comparison](visualization/github/cases/CT_8/comparison.png) |
| 26 | 79.37% | 81.14% | [View comparison](visualization/github/cases/CT_26/comparison.png) |
| 25 | 80.87% | 82.43% | [View comparison](visualization/github/cases/CT_25/comparison.png) |
| 22 | 83.33% | 84.45% | [View comparison](visualization/github/cases/CT_22/comparison.png) |
| 18 | 87.04% | 87.24% | [View comparison](visualization/github/cases/CT_18/comparison.png) |
| 1 | 88.00% | 88.11% | [View comparison](visualization/github/cases/CT_1/comparison.png) |
| 5 | 90.37% | 90.25% | [View comparison](visualization/github/cases/CT_5/comparison.png) |
| 2 | 92.16% | 92.26% | [View comparison](visualization/github/cases/CT_2/comparison.png) |

### Segmentation and scoring techniques

The implementation processes each CT slice independently. It converts stored pixel values to Hounsfield Units (HU), applies a 3×3 median filter, selects the inclusive 50–200 HU range, performs 5×5 disk opening, keeps the largest 8-connected component, then performs 5×5 disk closing. The fixed settings are in [`configs/paper_protocol.yaml`](configs/paper_protocol.yaml); the [paper method mapping](docs/PAPER_IMPLEMENTATION_MAP.md) and [reproduction gaps](docs/REPRODUCTION_GAPS.md) explain choices the paper leaves unspecified. No parameter search or manual mask correction is used.

Dice measures overlap of the liver masks. Liver IoU measures liver intersection over union; background IoU measures the same for non-liver pixels; mIoU is the arithmetic mean of the two class IoUs. Scores in CSV and JSON files are fractions, while the README and figures show percentages. Headline metrics score each patient's entire volume before averaging the 20 patient scores equally. The summary file also reports slice-averaged and pooled alternatives; keep these aggregation conventions distinct when comparing numbers.

For local regeneration, follow the [run instructions](#run) and use `python run.py evaluate --workers 6`, `python run.py report`, and `python run.py visualization --workers 6`. These commands use the labelled CT training-set data in `DATASET/CHAOS_Train_Sets/Train_Sets/CT`; they do not use the separate test download. The curated GitHub gallery remains under `visualization/github/`.


## Method

```text
Raw CT DICOM
    ↓ pixel × RescaleSlope + RescaleIntercept
HU image
    ↓ 3×3 median filter
Inclusive 50–200 HU band
    ↓ 5×5 disk opening
Largest 2D connected component (8-neighbour)
    ↓ 5×5 disk closing
Predicted liver mask
```

This follows Section 4.2 and the Figure 3 description. The paper's Section 3 ordering differs, and it does not specify kernels, border handling or connectivity. Our documented defaults are 3×3 median with reflect padding, radius-2 discrete disk for morphology, zero morphology borders, and 8-connectivity. Exact author-code equivalence cannot be established. See [paper verification](docs/PAPER_VERIFICATION.md), [code mapping](docs/PAPER_IMPLEMENTATION_MAP.md) and [assumptions with reasons](docs/REPRODUCTION_GAPS.md).

Original CT is already single-channel, so no RGB conversion is performed. HU values are never inferred from display PNGs. Each slice is processed independently; no 3D refinement or neural network is used. Display windowing is applied only when creating pictures.

## Open in VS Code

Open `STEGO_IMPLEMENTATION_USINGHU.code-workspace` or this folder. Select your Python interpreter. The Run and Debug panel has configurations for audit, fixed paper evaluation, patient visualization and tests. The evaluation debugger uses one worker and the SciPy reference backend. The CLI uses a tested equivalent OpenCV morphology/component backend for speed.

```text
configs/paper_protocol.yaml       Fixed segmentation parameters
configs/alignment_overrides.yaml  Recorded anatomical alignment decision
src/io_chaos.py                   CT/GT audit and HU conversion
src/pipeline.py                   Slice segmentation and intermediate stages
src/metrics.py                    Dice, IoU components and mIoU
src/run_experiment.py             Evaluation and CSV/JSON output
src/export_segmentations.py       Patient masks and comparison figures
src/make_figures.py               Six-stage paper-style figure
src/diagnostics.py                Dataset HU histogram and alignment figure
src/check_integrity.py            Original-source and metric verification
src/verify.py                     Deterministic rerun verification
src/report.py                     Dice/mIoU results report
tests/                           Unit and audited-data checks
reports/paper_protocol/           Measured results
visualization/                   Patient segmentation images
DATASET/                         Original local data, never modified
```

## Quick start after cloning

```sh
git clone https://github.com/Jaideep3020/stego_huimplementation.git
cd stego_huimplementation
python -m venv .venv
```

On Windows use `.venv\Scripts\python.exe`; on macOS/Linux use `.venv/bin/python` for the next commands. Select that interpreter in VS Code. Install the pinned dependencies, copy the CT dataset to the documented layout, and run:

```sh
python -m pip install -r requirements.txt
python run.py all --workers 6
```

The two commands above assume the virtual environment is active. Alternatively use the explicit environment interpreter paths from [the cross-platform setup guide](docs/CLONE_AND_RUN.md). `git clone` supplies the implementation, evaluation tables, and curated visualization package; the full CT dataset and complete local export are not stored in Git.

## Run

Use the project root as the working directory. The numerical/image dependencies are pinned in `requirements.txt`; the recorded environment uses Python 3.14.5.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make all WORKERS=6
```

The moved local input is `DATASET/CHAOS_Train_Sets/Train_Sets/CT`; the separate test download is `DATASET/CHAOS_Test_Sets/Test_Sets/CT`. Current evaluation uses the 20 labelled CT patients from the CHAOS training download; it does not use the separate CHAOS test download. No download is needed on this machine. Each phase can also run separately:

```sh
make audit           # CT/GT files, HU tags, counts, labels, ordering and fingerprints
make test            # Standard-library unittest; also available in VS Code Testing
make evaluate        # Fixed method on all patients
make diagnostics     # Dataset histogram and alignment evidence
make figures         # Paper-style intermediate-stage figure
make visualization   # All patient masks and comparison pictures
make integrity       # Fresh original-DICOM prediction with the SciPy backend
make verify          # Byte-identical repeated evaluation
make report          # Results report
make export          # Visualization folder plus visualization.zip
```

To regenerate just the complete evaluation tables and report, run `python run.py evaluate --workers 6` followed by `python run.py report`. To regenerate patient overlays and masks, run `python run.py visualization --workers 6`; this writes the local `visualization/` export. The curated 15-case GitHub bundle is maintained separately under `visualization/github/` so regeneration of the full local export does not define which examples are selected for publication. `python run.py all --workers 6` runs the full audit, tests, evaluation, figures, export, integrity checks, verification, and report.

For different input, set `data` in `configs/paper_protocol.yaml` and use `make all`, or run `python3 -m src.io_chaos --data /path/to/CT` before evaluation. Do not run the audit while experiments are active. Changing source files invalidates affected cached median volumes; changing the median implementation itself requires removing its cached `*_med*.npy` files.

## Scores

- Dice = 2TP/(2TP+FP+FN).
- Liver IoU = TP/(TP+FP+FN).
- Background IoU = TN/(TN+FP+FN).
- mIoU = (liver IoU + background IoU)/2.

Headline scores are calculated over each patient's complete volume, then averaged equally over patients. Population SD is reported. Empty/empty Dice and class IoU are 1. CSV/JSON values are fractions; Markdown uses percent. IoU components and TP/FP/FN/TN are retained so the requested mIoU can be checked. mIoU was requested by the user; it is not reported in the paper.

`reports/paper_protocol/per_patient.csv`, `per_slice.csv` and `summary.json` contain the measured results. The summary includes labelled secondary slice/pooled conventions. `reports/REPRODUCTION_REPORT.md` presents Dice and mIoU with parameters and limitations.

## Patient visualizations

```text
visualization/
  CT_1/
    masks/                Predicted liver masks, PNG 0/255
    ground_truth/         Matched reference masks, PNG 0/255
    segmented_ct/         CT display pixels inside the predicted mask
    mask_volume.npz       Boolean mask array [slice, row, column]
    slice_map.csv         Mapping to original DICOM and GT filenames
    metadata.json         Parameters, spacing and source fingerprint
  CT_<other patients>/
  comparisons/            Five slices per patient
  scores/                 Measured Dice/mIoU CSVs and configuration
  preview.png             One representative slice
  export_verification.json
```

Comparison columns: original CT, ground truth, paper-method prediction and errors. Green is correct liver, red is extra prediction, blue is missed liver. CT display window is -100 to 300 HU; these PNGs are display images, not quantitative HU volumes. Every exported prediction is checked against measured confusion counts and round-tripped through PNG/NPZ.

## Alignment and integrity

All final masks retain forward ordering. A rough-band heuristic incorrectly proposed reversing CT14; visual anatomy supports forward ordering, recorded explicitly in `configs/alignment_overrides.yaml`. See `reports/figures/alignment_CT_14.png` and the audit manifest. No predicted masks are manually corrected.

`make integrity` rereads original DICOM and GT files, checks SHA256 and cache equality, recomputes predictions with fresh filtering and the SciPy reference backend, independently counts errors, and compares Dice/mIoU with saved results. `make verify` repeats the fixed evaluation and compares exact CSV/JSON bytes. These establish computational consistency; anatomical annotation correctness requires separate review.

## Clone on another PC

See [CLONE_AND_RUN.md](docs/CLONE_AND_RUN.md) for Windows, macOS and Linux setup. `python run.py all --workers 6` is the cross-platform alternative to Make. The repository includes source, tests, configuration and compact measured results; copy the original CT data separately. Generated visualizations and caches are rebuilt locally and excluded from Git.

## Development and checks

Run `python run.py test` for the unit suite. GitHub Actions runs those tests on Linux, Windows and macOS without the dataset; the real-data integration test skips until CT input is audited locally. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Paper reference

Rohini A. Bhusnurmath and Shivaleela Betageri. *Hounsfield Unit Based Multi-Threshold Approach for Liver Segmentation*. Procedia Computer Science 258 (2025), 3804–3813. DOI: [10.1016/j.procs.2025.04.635](https://doi.org/10.1016/j.procs.2025.04.635).

This repository is an independent implementation. The paper's authors and dataset providers retain attribution for their respective work; the original paper, dataset and author source code are not redistributed here.
