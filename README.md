# HU-based liver segmentation on CHAOS CT

[![Tests](https://github.com/Jaideep3020/stego_huimplementation/actions/workflows/tests.yml/badge.svg)](https://github.com/Jaideep3020/stego_huimplementation/actions/workflows/tests.yml)

A structured implementation of the HU-based liver segmentation method described by Bhusnurmath & Betageri, *Hounsfield Unit Based Multi-Threshold Approach for Liver Segmentation*, Procedia Computer Science 258 (2025), 3804–3813, [DOI](https://doi.org/10.1016/j.procs.2025.04.635).

The project applies **one fixed paper-method configuration** to all **20 labelled local CT patients and 2,874 slices**. The requested outputs are **Dice, mIoU, and patient segmentation visualizations**. MRI is excluded. Parameters are not tuned.


## Measured results

| Metric | Mean over 20 complete patient volumes |
|---|---:|
| Dice | **71.25%** |
| mIoU, liver + background | **76.24%** |

These are measured results from this implementation, not the paper's reported values. mIoU includes liver and background; its component IoUs and confusion counts are saved for inspection. See [the results report](reports/REPRODUCTION_REPORT.md) and [per-patient CSV](reports/paper_protocol/per_patient.csv).


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

The two commands above assume the virtual environment is active. Alternatively use the explicit environment interpreter paths from [the cross-platform setup guide](docs/CLONE_AND_RUN.md). `git clone` supplies the implementation and compact results; the CT dataset and generated images are not stored in Git.

## Run

Use the project root as the working directory. The numerical/image dependencies are pinned in `requirements.txt`; the recorded environment uses Python 3.14.5.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make all WORKERS=6
```

Existing input is `DATASET/CHAOS_Train_Sets/Train_Sets/CT`. No download is needed. Each phase can also run separately:

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
