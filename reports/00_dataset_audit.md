# CT dataset audit

Source: `DATASET/CHAOS_Train_Sets/Train_Sets/CT`. MRI and test archives were not read.

20 labelled CT patients; 2874 slices. All CT/GT counts, shapes, HU tags, binary encodings (0/1 or 0/255), and independent GT voxel counts passed.

CT images are single-channel 512×512, 16-bit DICOM. GT PNG values were checked across every mask (actual values recorded in the manifest).

GT filenames use numeric sorting. DICOM uses InstanceNumber (z fallback). The central-half rough-band overlap chooses forward/reversed GT order; this is a heuristic alignment check, not independent registration evidence. Explicit visually justified overrides take precedence over the overlap heuristic. Every decision, override and source SHA256 is recorded in dataset_manifest.json.

| Patient | Slices | Pixel spacing mm | z spacing mm | Forward overlap | Reversed overlap | GT flipped |
|---|---:|---|---|---:|---:|---|
| 1 | 96 | [0.687671, 0.687671] | 1.500–1.500 | 0.58693 | 0.46324 | False |
| 2 | 81 | [0.77734375, 0.77734375] | 2.000–2.000 | 0.59245 | 0.41877 | False |
| 5 | 95 | [0.755859375, 0.755859375] | 1.600–1.600 | 0.66958 | 0.56528 | False |
| 6 | 88 | [0.649549, 0.649549] | 1.500–1.500 | 0.67681 | 0.61485 | False |
| 8 | 123 | [0.734375, 0.734375] | 1.600–1.600 | 0.52716 | 0.32802 | False |
| 10 | 110 | [0.693359375, 0.693359375] | 1.600–1.600 | 0.62495 | 0.48685 | False |
| 14 | 95 | [0.568359375, 0.568359375] | 1.600–1.600 | 0.16232 | 0.21923 | False |
| 16 | 91 | [0.791015625, 0.791015625] | 2.000–2.000 | 0.54655 | 0.45710 | False |
| 18 | 111 | [0.68359375, 0.68359375] | 1.600–1.600 | 0.61127 | 0.51700 | False |
| 19 | 90 | [0.666015625, 0.666015625] | 1.600–1.600 | 0.53151 | 0.47749 | False |
| 21 | 257 | [0.78125, 0.78125] | 1.000–1.000 | 0.64623 | 0.48108 | False |
| 22 | 101 | [0.72265625, 0.72265625] | 1.600–1.600 | 0.59705 | 0.43131 | False |
| 23 | 240 | [0.658203125, 0.658203125] | 1.000–1.000 | 0.49212 | 0.38562 | False |
| 24 | 123 | [0.63671875, 0.63671875] | 2.000–2.000 | 0.46168 | 0.32128 | False |
| 25 | 235 | [0.6015625, 0.6015625] | 1.000–1.000 | 0.57318 | 0.11493 | False |
| 26 | 114 | [0.76171875, 0.76171875] | 1.600–1.600 | 0.57065 | 0.41455 | False |
| 27 | 242 | [0.68359375, 0.68359375] | 1.000–1.000 | 0.57225 | 0.39469 | False |
| 28 | 102 | [0.693359375, 0.693359375] | 1.600–1.600 | 0.50738 | 0.41769 | False |
| 29 | 214 | [0.68359375, 0.68359375] | 1.000–1.000 | 0.50621 | 0.40320 | False |
| 30 | 266 | [0.732421875, 0.732421875] | 1.000–1.000 | 0.60836 | 0.40904 | False |

Alignment overrides: {"14": {"order": "forward", "reason": "Visual CT/GT overlays show forward masks follow the liver boundary; reversed masks cross the body boundary. Rough HU overlap falsely prefers reversal because this enhanced liver is mostly above the threshold band.", "evidence": "reports/figures/alignment_CT_14.png"}}

Actual slice counts and spacings above take precedence over the estimates in the supplied plan.

Pooled GT liver HU: {"mean": 129.0230712890625, "std": 38.898193359375, "p01": 33.0, "p99": 241.0}

Physical volumes use pixel area × midpoint slice extents; z spacing rather than SliceThickness determines voxel extent.
