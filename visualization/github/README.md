# Repository visualization and evaluation artifacts

This folder contains 15 demonstrative CHAOS CT cases, alongside evaluation output for the complete analyzed cohort: all 20 patients and all 2,874 slices. The selection only limits the visualization examples; it does not limit the evaluation tables.

## Contents

- `cases/CT_<id>/comparison.png`: five representative GT-positive slices, aligned in the same pixel coordinates. Columns show CT, reference mask, prediction, full contours, and pixel-wise errors. Patient-volume Dice and mIoU appear in the figure title.
- `cases/CT_<id>/predicted_mask_volume.npz`: boolean prediction volume with array key `mask`, ordered `[slice, row, column]`; this contains every slice for that selected case. Ground-truth masks and source DICOMs are not copied here.
- `cases/CT_<id>/metrics.json`: patient-volume counts and scores for that case.
- `evaluation/per_patient.csv`: metrics and confusion counts for all 20 patients.
- `evaluation/per_slice.csv`: metrics and confusion counts for all 2,874 slices.
- `evaluation/summary.json`: cohort-level patient-mean, slice-mean, and pooled metrics with aggregation conventions.
- `evaluation/config.yaml`: fixed HU segmentation configuration.
- `selection.json`: reproducible case selection method and selected case scores.

The 15 displayed cases are sampled at evenly spaced ranks after sorting the 20 patients by patient-volume Dice, so examples span the measured range.

## Headline cohort result

Patient-volume means (each patient's full volume is scored, then patients are averaged):

- Dice: 71.25% (20 patients)
- Two-class mIoU: 76.24% (20 patients)

The per-slice and pooled figures differ by aggregation method; consult `summary.json` for those definitions.

## CHAOS dataset attribution

Source: Kavur et al., *CHAOS - Combined (CT-MR) Healthy Abdominal Organ Segmentation Challenge Data*, DOI [10.5281/zenodo.3431873](https://doi.org/10.5281/zenodo.3431873). The dataset is distributed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The figures and masks here are adapted outputs from the CHAOS CT training data, processed with the HU-threshold pipeline documented in this repository. We credit the dataset authors and link the source and license; the source DICOM series and reference-mask files are not redistributed here. Use and redistribution of these adapted dataset-derived artifacts must follow the dataset license, including its noncommercial and share-alike terms.

The CT comparison figures and predictions are derived from the CHAOS training data and processed using the fixed HU threshold pipeline documented in the project. These results are research artifacts, not clinical tools.
