# Results and analysis

## Scope

This analysis summarizes the fixed HU threshold pipeline on all 20 labelled CHAOS CT training-set patients (2,874 slices). Each patient's complete volume is scored first; the headline result is the equal-patient mean. The source tables are [the per-patient matrix](../visualization/github/evaluation/per_patient.csv), [the per-slice matrix](../visualization/github/evaluation/per_slice.csv), and [the aggregation summary](../visualization/github/evaluation/summary.json).

The method uses one unmodified configuration for every case: HU conversion, 3×3 median filtering, an inclusive 50–200 HU range, 5×5 disk opening, largest 8-connected component selection, and 5×5 disk closing. It processes each CT slice independently. There is no parameter tuning, learned model, or manual mask correction.

## Headline results

| Metric | Equal-patient mean | Population SD | Median | Range |
|---|---:|---:|---:|---:|
| Dice | 71.25% | 19.17 points | 73.56% | 6.46%–92.16% |
| Liver IoU | 58.21% | 19.68 points | 58.18% | 3.34%–85.46% |
| Background IoU | 94.27% | 4.42 points | 96.21% | 82.10%–99.06% |
| Two-class mIoU | 76.24% | 11.91 points | 77.26% | 42.72%–92.26% |

Dice is the overlap of the predicted and reference liver masks. Liver IoU measures liver overlap only. Background IoU measures agreement on non-liver pixels. Two-class mIoU is the arithmetic mean of liver IoU and background IoU.

The pooled-voxel result is lower than the equal-patient headline: Dice 69.54%, liver IoU 53.30%, background IoU 94.63%, and mIoU 73.97%. These are different aggregation conventions: pooled voxels give larger scans more weight, whereas the headline gives each patient equal weight. They should not be mixed in comparisons.

## Interpretation

The method performs strongly for some cases: 8 of 20 patients have Dice at or above 80%, and the best case, CT 2, reaches 92.16% Dice and 92.26% mIoU. The high background IoU across the cohort reflects that non-liver pixels make up most CT pixels.

Liver segmentation is the harder part. Liver IoU is consistently lower than background IoU and drives the variation in Dice and mIoU. Four cases have Dice below 60%. CT 14 is the main failure case at 6.46% Dice and 3.34% liver IoU. The saved overlays make this visible rather than hiding it behind the cohort mean.

The low-performing cases also show that excess predicted area is a recurring error mode. CT 24 has 49.73% Dice despite only 6,617 false-negative pixels because it contains 3,853,108 false-positive pixels. CT 19, CT 23, and CT 29 similarly have many more false positives than false negatives. This is consistent with a fixed HU band selecting non-liver tissues with similar attenuation. These observations identify limitations of this rule-based method; they do not establish a clinical failure mode.

## Visual review

Open the [visualization gallery](../visualization_gallery/README.md) to inspect the 15 selected cases directly in GitHub. The cases are selected from evenly spaced ranks after sorting all 20 patients by Dice, so the gallery contains low, middle, and high scoring examples rather than only favorable images.

Each comparison image contains five slices. Columns show the CT image, reference mask, prediction, contour overlay, and pixel-wise error map. Green means correctly predicted liver, red means false positive, blue means missed liver, and yellow in the contour panel means coincident reference and predicted boundaries. The CT display window is −100 to 300 HU and does not alter segmentation or scoring.

## Limitations

- The data are the labelled CHAOS CT training-set patients; the separate CHAOS test download is not evaluated here.
- The method is a 2D fixed-threshold rule. It uses no 3D context, learned appearance model, or case-specific tuning.
- The paper does not fully specify several implementation choices, including morphology details and aggregation. The chosen settings are recorded in [`configs/paper_protocol.yaml`](../configs/paper_protocol.yaml) and explained in [the reproduction gaps](REPRODUCTION_GAPS.md).
- These metrics describe agreement with the available reference masks in this cohort. They are research results, not clinical validation.

## Reproduce

From the repository root, run:

```sh
python run.py evaluate --workers 6
python run.py report
python run.py visualization --workers 6
```

The input path is `DATASET/CHAOS_Train_Sets/Train_Sets/CT`. The complete workflow is documented in the [README](../README.md).
