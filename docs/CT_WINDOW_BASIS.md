# Basis for CT visualization windows

Windowing changes display contrast only. It does not change the HU values fed to segmentation, the fixed 50–200 HU band, masks, Dice, or mIoU.

The user-supplied screenshot gives two symmetric display intervals:

- WW 150 / WL 60: WL ± WW/2 = -15 to 135 HU.
- WW 120 / WL 40: WL ± WW/2 = -20 to 100 HU.

These arithmetic intervals are valid for symmetric linear clipping. They are not evidence that either pair is universally optimal or was used in the reproduced paper. Exact DICOM default LINEAR mapping includes half-unit/width-minus-one conventions; LINEAR_EXACT uses the symmetric mapping. A display implementation should name its mapping explicitly.

## Published support and its limits

[Okimoto et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11341740/) describes conventional liver WW150 with commonly used levels in the 50–100 HU range. Thus WL60 is a defensible example within that range. The study investigates a different task, HCC detection with contrast-enhanced CT and deep-learning reconstruction, and uses WW120 with WL90 for its default image-quality comparison. It does not establish WW120/WL40 as universal or either preset as optimal for whole-liver segmentation displays.

[DICOM PS3.3 C.11.2](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.11.2.html) defines Window Center/Width as display transforms applied after rescaling, and supports alternative paired presets.

## Local dataset evidence

The first stored DICOM presets across these cases have WW350–400 and WL45–60. Some cases contain an additional paired alternative. Header values are dataset-based display settings, not proof of clinical optimality.

In CT14, 97.5948% of GT liver voxels exceed 135 HU. A symmetric WW150/WL60 display therefore saturates almost all of its annotated liver white. The WW120/WL40 upper bound of 100 HU clips 98.9425%. This makes a single narrow preset unsuitable as a universal view for this enhanced case.

`reports/window_display_review.csv` records the first stored preset and above-bound liver fractions for every patient. `visualization/window_comparison.png` shows identical CT pixels and GT contours under the existing broad window, both suggested narrow windows, and the first stored DICOM preset. Slice selection is the largest GT-area slice for CT1, CT14 and CT28.

No segmentation parameter, mask, score, or existing primary visualization default was changed by this comparison. A dedicated liver view can be offered as an additional labelled preset, with the broader or stored DICOM view retained for highly enhanced cases. The segmentation paper's actual display window remains unspecified.
