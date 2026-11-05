# Paper-method liver segmentation: Dice and mIoU

All **20 labelled CT patients and 2874 slices** are included.

| Metric | Patient mean % | Patient SD (percentage points) |
|---|---:|---:|
| Dice | 71.2483 | 19.1673 |
| mIoU (liver + background) | 76.2387 | 11.9060 |

Each patient is scored over its complete volume, then patient scores are averaged equally. SD uses ddof=0. CSV/JSON values are fractions; this report uses percent.
