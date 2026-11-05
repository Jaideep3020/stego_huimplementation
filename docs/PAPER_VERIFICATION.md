# Verification against the paper

Bhusnurmath & Betageri, *Hounsfield Unit Based Multi-Threshold Approach for Liver Segmentation*, Procedia Computer Science 258 (2025), 3804–3813. [DOI](https://doi.org/10.1016/j.procs.2025.04.635), [publisher PDF](https://www.sciencedirect.com/science/article/pii/S1877050925017399/pdf).

The publisher's 10-page PDF text and user-supplied methodology screenshots were reviewed. Author source code was not available for comparison.

- Section 3: independent 2D CT slices, HU conversion, median filtering, bounded threshold and largest-component selection with morphological post-processing.
- Section 4.2: bounds are 50 and 200 HU; explicit order is threshold → opening → largest component → closing. This is the implemented fixed configuration.
- Section 3's ordering differs from 4.2. The configuration labels that choice `fig3`; a unit test also demonstrates the alternative order's behavior.
- Morphology equations in the supplied screenshot confirm closing = dilation then erosion, opening = erosion then dilation.
- The paper does not give median/morphology kernel sizes, footprint shape, connectivity, border rules or metric aggregation.
- The colour-input statement conflicts with native CT DICOM. The implementation preserves single-channel pixels and DICOM HU metadata.
- Local CT slice counts are 81–266, differing from the paper's 77–105 estimate. All 20 local cases and all 2,874 slices are included; exact author-evaluated image correspondence is unknown.
- Dice uses the paper's formula. Two-class mIoU is an additional user-requested evaluation metric.

The requested scope is one fixed paper-method segmentation, Dice, mIoU and visualization. No parameters are tuned. Exact author-code equivalence remains unestablished because missing methodological details cannot be inferred from the paper's final scores.
