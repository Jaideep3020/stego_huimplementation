# Unspecified settings and implementation decisions

Sources: supplied methodology screenshots and the checked [paper](https://doi.org/10.1016/j.procs.2025.04.635). These are declared defaults, not confirmed author settings or claims of optimality.

| Missing/conflicting detail | Fixed choice | Why chosen |
|---|---|---|
| Order differs between Sections 3 and 4.2 | Threshold → opening → largest component → closing | Section 4.2 explicitly explains Figure 3's results |
| Median size absent | 3×3 | Small neighbourhood, modest noise filtering |
| Median borders absent | Reflect | Extends nearby values without introducing a constant HU |
| Morphology size absent | 5×5 opening and closing | Modest smoothing footprint; same baseline size avoids extra assumptions |
| Morphology shape absent | Discrete disk, radius 2 | Symmetric footprint without square corners |
| Morphology borders absent | Constant zero | Explicit outside-image background |
| Connectivity absent | 8-neighbour | Retains diagonally touching pixels |
| Component ties absent | First in raster order | Deterministic and consistent across backends |
| RGB description conflicts with raw CT | Use single-channel DICOM | Preserves pixels and metadata required for HU |
| Exact evaluated case/slice list absent | All 20 local cases, 2874 slices | No favourable slice selection or silent exclusions |
| Pairing procedure absent | DICOM InstanceNumber (z fallback), numeric GT ordering | Explicit reproducible association, with recorded visual review |
| Rough-band heuristic incorrectly reverses CT14 | Preserve forward GT ordering by visual evidence | Forward contours follow liver anatomy; reversed contours do not |
| Patient/slice aggregation absent | Whole-volume scores, then equal patient mean | Every patient has equal weight |
| Empty sets unspecified | Empty/empty Dice and class IoU = 1 | Both masks agree that the class is absent |
| SD convention absent | Population SD, ddof=0 | Describes variation across the evaluated cases explicitly |
| Author software details unavailable | Pinned dependencies, SciPy reference, tested OpenCV acceleration | Reproducible code and independently checked numerical agreement |

## Settings directly supported by the paper

CT only; independent 2D slices; HU = pixel × slope + intercept; median after HU scaling; inclusive 50–200 HU band (Section 4.2); largest component by pixel count; standard opening and closing definitions. Parameters are held fixed for every patient.

## Requested scores

Dice is the paper's overlap metric. mIoU is requested by the user and averages liver IoU with background IoU. Headline values average whole-patient scores. Component IoUs and confusion counts remain available for audit.

## Visualization choices

- CT window -100 to 300 HU: consistent display, never segmentation input.
- White/black masks: foreground/background.
- Green overlay: correct liver; red: false positive; blue: false negative; opacity .6.
- Preview patient: lower-median patient Dice; preview slice: largest GT area. This is not selection by the best slice score.
- Patient comparison: five evenly spaced GT-positive slice indices.
- Titles show whole-patient Dice and mIoU.

The authors' undocumented settings, exact evaluated image subset and original code cannot be reconstructed uniquely from their headline scores. Their configuration/source and case manifest would be needed to settle those gaps. No manual predicted-mask correction, ROI restriction, neural network or 3D refinement is added.
