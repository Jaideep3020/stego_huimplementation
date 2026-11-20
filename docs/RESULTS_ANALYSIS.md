# Results Analysis

## Cohort and configuration

This analysis covers all 20 labelled CHAOS CT training-set patients and 2,874 slices. The fixed pipeline uses an inclusive 40–180 HU threshold, no median filter, no opening, largest 8-connected component selection, and 7×7 disk closing. Each slice is processed independently.

The evidence files are the [per-patient matrix](../visualization/github/evaluation/per_patient.csv), [per-slice matrix](../visualization/github/evaluation/per_slice.csv), and [summary](../visualization/github/evaluation/summary.json).

## Headline results

The primary result computes metrics for each patient’s complete volume and then averages the 20 patient scores equally.

| Metric | Mean | Sample SD | Median | Range |
|---|---:|---:|---:|---:|
| Dice | 56.92% | 17.69 points | 58.49% | 4.10%–82.58% |
| Liver IoU | 41.64% | 16.04 points | 41.36% | 2.09%–70.32% |
| Background IoU | 89.31% | 5.97 points | 90.30% | 75.00%–97.68% |
| Two-class mIoU | 65.47% | 10.79 points | 65.60% | 38.54%–84.00% |

The pooled-voxel calculation is lower: Dice 53.94%, liver IoU 36.93%, background IoU 89.65%, and mIoU 63.29%. Pooled results weight larger scans more heavily; the headline treats every patient equally.

## Interpretation

The performance range is wide. CT 2 is the strongest case with 82.58% Dice and 84.00% mIoU. CT 14 is the weakest case with 4.10% Dice and 38.54% mIoU. Ten of 20 patients score below 60% Dice, while one patient reaches 80% Dice.

Background IoU is much higher than liver IoU throughout the cohort. This means the threshold rule identifies non-liver pixels more reliably than it isolates liver tissue. In lower-performing cases, false positives are a recurring pattern: nearby tissues can share HU values inside the fixed threshold interval.

The [visualization gallery](../visualization_gallery/README.md) shows this range directly. Its 15 cases are selected at evenly spaced positions after ranking all 20 patients by Dice, so it includes low, middle, and high outcomes rather than hand-picked favorable examples.

## Interpretation limits

- The evaluation uses the labelled CHAOS CT training-set cohort, not the separate CHAOS test download.
- The pipeline has no learned model, 3D context, or case-specific adjustment.
- The paper does not specify every morphology and aggregation detail; the recorded choices are in [`configs/paper_protocol.yaml`](../configs/paper_protocol.yaml) and [the reproduction gaps](REPRODUCTION_GAPS.md).
- Metrics describe agreement with the available reference masks in this dataset. They do not establish clinical performance.

## Reproduce

Run from the repository root after placing the CT data at `DATASET/CHAOS_Train_Sets/Train_Sets/CT`:

```sh
python run.py evaluate --workers 6
python run.py report
python run.py visualization --workers 6
python -m src.export_github_gallery
```
