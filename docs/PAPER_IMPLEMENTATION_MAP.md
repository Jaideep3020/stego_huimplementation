# Paper-to-code map

The [publisher PDF](https://www.sciencedirect.com/science/article/pii/S1877050925017399/pdf) text and supplied screenshots were checked. Section 4.2 explicitly gives 50–200 HU and threshold → opening → largest component → closing. This project implements that fixed sequence for every patient.

| Stage | Code | Paper relationship |
|---|---|---|
| Input | `io_chaos.py:patients`, `read_patient` | Labelled CHAOS CT; all local cases/slices included |
| HU conversion | `io_chaos.py:hu_from_dicom` | Equation 2, explicit slope and intercept |
| Median | `pipeline.py:stages` | Section 3.2.3; 3×3/reflect borders are documented defaults |
| Threshold | `pipeline.py:stages` | Inclusive bounds in Section 3.3; 50 and 200 in Section 4.2 |
| Opening | `pipeline.py:morph` | Erosion then dilation; radius-2 disk assumed |
| Largest component | `pipeline.py:largest_component` | Most foreground pixels; 8-connectivity assumed |
| Closing | `pipeline.py:morph` | Dilation then erosion; same disk assumed |
| Volume | `pipeline.py:segment_volume` | Independent 2D slices, no 3D processing |
| Dice | `metrics.py:from_confusion` | Paper's Equation 7 |
| mIoU | `metrics.py:from_confusion` | Additional requested metric; mean of liver and background IoU |
| Evaluation | `run_experiment.py` | Same fixed parameters for every patient; equal patient weighting |
| Pictures | `export_segmentations.py`, `make_figures.py` | Patient results and paper-style intermediate stages |

The code retains configurable kernel/connectivity/order options so assumptions are visible and the Section 3/4 ordering ambiguity can be inspected. The shipped evaluation executes only the fixed configuration in `configs/paper_protocol.yaml`; there is no search or patient-specific parameter selection.

Example:

```python
import numpy as np
from src.pipeline import stages

hu = np.load('reports/cache/1_hu.npy', mmap_mode='r')
result = stages(hu[20])
mask = result['final']
```

CT14's original forward GT ordering is preserved by an explicitly recorded visual override. Unknown author kernels and unavailable author code prevent certification of exact numerical equivalence. See `REPRODUCTION_GAPS.md`.
