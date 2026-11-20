# HU-only segmentation adaptation: Dice and mIoU

All **20 labelled CT patients and 2874 slices** are included.

| Metric | Patient mean % | Patient SD (percentage points) |
|---|---:|---:|
| Dice | 56.9213 | 17.6908 |
| mIoU (liver + background) | 65.4740 | 10.7905 |

Each patient is scored over its complete volume, then patient scores are averaged equally. SD uses ddof=1 (sample SD). CSV/JSON values are fractions; this report uses percent.
