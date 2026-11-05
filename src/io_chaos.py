"""Strict CT input validation and explicitly recorded mask ordering."""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pydicom
import yaml
from PIL import Image

DEFAULT_DATA = 'DATASET/CHAOS_Train_Sets/Train_Sets/CT'


def natural_key(path):
    return [int(v) if v.isdigit() else v.lower() for v in re.split(r'(\d+)', str(path))]


def hu_from_dicom(ds):
    if ds.Modality != 'CT':
        raise ValueError('Only CT is supported; MRI intensities are not HU')
    if not all(hasattr(ds, k) for k in ('RescaleSlope', 'RescaleIntercept')):
        raise ValueError('CT must contain explicit HU rescale tags')
    if getattr(ds, 'SamplesPerPixel', 1) != 1:
        raise ValueError('Expected single-channel CT')
    return ds.pixel_array.astype(np.float32) * float(ds.RescaleSlope) + float(ds.RescaleIntercept)


def patients(root):
    root = Path(root)
    if root.name.upper() != 'CT':
        raise ValueError('Point --data at the CT directory, not MR or a test archive')
    result = sorted([p for p in root.iterdir() if p.is_dir() and (p / 'DICOM_anon').is_dir()], key=natural_key)
    if not result:
        raise ValueError(f'No labelled CT patients in {root}')
    return result


def read_patient(path, alignment_overrides=None):
    path = Path(path)
    files = sorted([p for p in (path / 'DICOM_anon').rglob('*') if p.is_file() and not p.name.startswith('.')], key=natural_key)
    ds = [pydicom.dcmread(p) for p in files]
    if all(hasattr(d, 'InstanceNumber') for d in ds):
        order = sorted(range(len(ds)), key=lambda i: int(ds[i].InstanceNumber))
        assert len(set(int(d.InstanceNumber) for d in ds)) == len(ds), 'Duplicate InstanceNumber'
        sort_tag = 'InstanceNumber'
    else:
        order = sorted(range(len(ds)), key=lambda i: float(ds[i].ImagePositionPatient[2]))
        sort_tag = 'ImagePositionPatient.z'
    ds, files = [ds[i] for i in order], [files[i] for i in order]
    gt_files = sorted((path / 'Ground').glob('*.png'), key=natural_key)
    assert len(ds) == len(gt_files) > 0, f'{path.name}: CT/GT count mismatch'
    arrays = [np.asarray(Image.open(p)) for p in gt_files]
    values = sorted(set(int(v) for a in arrays for v in np.unique(a)))
    assert set(values) <= {0, 255} or set(values) <= {0, 1}, f'Unexpected GT values: {values}'
    foreground = max(values)
    assert foreground in (1, 255), 'Patient has no labelled liver'
    gt = np.stack([a == foreground for a in arrays])
    # Independent sum of source intensities must agree with boolean voxel counts.
    independent_count = sum(int(np.sum(a, dtype=np.uint64)) // foreground for a in arrays)
    assert int(gt.sum()) == independent_count
    hu = np.stack([hu_from_dicom(d) for d in ds])
    assert hu.shape == gt.shape and hu.ndim == 3, f'{path.name}: image/mask shape mismatch'
    assert hu.shape[1:] == (512, 512), 'Unexpected slice size'
    assert all(int(d.BitsAllocated) == 16 for d in ds), 'Expected 16-bit CT'
    spacing_xy = [list(map(float, d.PixelSpacing)) for d in ds]
    assert np.allclose(spacing_xy, spacing_xy[0]), 'Variable in-plane spacing'
    z = np.array([float(d.ImagePositionPatient[2]) for d in ds])
    dz = np.abs(np.diff(z))
    assert np.all(dz > 0) and (np.all(np.diff(z) > 0) or np.all(np.diff(z) < 0)), 'Non-monotonic slices'
    # Use central half; a heuristic diagnostic, not a proof of anatomical registration.
    central = slice(len(ds) // 4, 3 * len(ds) // 4)
    rough = (hu >= 50) & (hu <= 200)
    def overlap(g):
        a, b = rough[central], g[central]
        return float(2 * np.count_nonzero(a & b) / max(1, np.count_nonzero(a) + np.count_nonzero(b)))
    forward, reverse = overlap(gt), overlap(gt[::-1])
    heuristic_flipped = reverse > forward + 1e-12
    override = (alignment_overrides or {}).get(path.name)
    if override and override["order"] not in ("forward", "reversed"):
        raise ValueError("Alignment override must be forward or reversed")
    flipped = override["order"] == "reversed" if override else heuristic_flipped
    if flipped:
        gt = gt[::-1].copy()
        gt_files = gt_files[::-1]
    fingerprint = hashlib.sha256()
    for dcm, mask in zip(files, gt_files):
        fingerprint.update(dcm.read_bytes())
        fingerprint.update(mask.read_bytes())
    meta = dict(patient=path.name, slices=len(ds), shape=list(hu.shape), bits_allocated=16,
                bits_stored=sorted(set(int(d.BitsStored) for d in ds)), gt_values=values,
                pixel_spacing_mm=spacing_xy[0], z_spacing_mm=dz.tolist(),
                slice_thickness_mm=sorted(set(float(d.SliceThickness) for d in ds)),
                uniform_z_spacing=bool(np.allclose(dz, dz[0])),
                sort_tag=sort_tag, alignment_forward=forward, alignment_reverse=reverse,
                gt_reversed=flipped, heuristic_gt_reversed=heuristic_flipped, alignment_override=override, alignment_margin=abs(forward-reverse),
                gt_voxels=independent_count, source_sha256=fingerprint.hexdigest(),
                dicom_files=[str(p) for p in files], gt_files=[str(p) for p in gt_files],
                slopes=sorted(set(float(d.RescaleSlope) for d in ds)),
                intercepts=sorted(set(float(d.RescaleIntercept) for d in ds)))
    # Midpoint-based slice extents for physical-volume integration (including end slices).
    meta['voxel_volumes_mm3'] = (np.r_[dz[0], (dz[:-1]+dz[1:])/2, dz[-1]] * np.prod(spacing_xy[0])).tolist()
    return hu, gt, meta


def audit(root=DEFAULT_DATA, out='reports', overrides_path='configs/alignment_overrides.yaml'):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cache = out / 'cache'
    cache.mkdir(exist_ok=True)
    previous_path = out / 'dataset_manifest.json'
    previous = {m['patient']: m['source_sha256'] for m in json.loads(previous_path.read_text())} if previous_path.exists() else {}
    overrides = yaml.safe_load(Path(overrides_path).read_text()) if Path(overrides_path).exists() else {}
    entries, stats, liver = [], {}, []
    for p in patients(root):
        hu, gt, meta = read_patient(p, overrides)
        if previous.get(p.name) != meta['source_sha256']:
            for stale in cache.glob(f'{p.name}_med*.npy'):
                stale.unlink()
        entries.append(meta)
        v = hu[gt]
        liver.append(v)
        stats[p.name] = dict(mean=float(v.mean()), std=float(v.std()), p01=float(np.percentile(v, 1)), p99=float(np.percentile(v, 99)))
        # .npy allows read-only mmap and keeps CPU workers from copying full volumes.
        np.save(cache / f'{p.name}_hu.npy', hu)
        np.save(cache / f'{p.name}_gt.npy', gt)
        print(f'Audited CT {p.name}: {len(hu)} slices, GT reversed={meta["gt_reversed"]}', flush=True)
    all_liver = np.concatenate(liver)
    stats['pooled'] = dict(mean=float(all_liver.mean()), std=float(all_liver.std()), p01=float(np.percentile(all_liver, 1)), p99=float(np.percentile(all_liver, 99)))
    (out / 'gt_liver_hu_stats.json').write_text(json.dumps(stats, indent=2))
    (out / 'dataset_manifest.json').write_text(json.dumps(entries, indent=2))
    lines = ['# CT dataset audit', '', f'Source: `{root}`. MRI and test archives were not read.', '',
             f'{len(entries)} labelled CT patients; {sum(e["slices"] for e in entries)} slices. All CT/GT counts, shapes, HU tags, binary encodings (0/1 or 0/255), and independent GT voxel counts passed.', '',
             'CT images are single-channel 512×512, 16-bit DICOM. GT PNG values were checked across every mask (actual values recorded in the manifest).', '',
             'GT filenames use numeric sorting. DICOM uses InstanceNumber (z fallback). The central-half rough-band overlap chooses forward/reversed GT order; this is a heuristic alignment check, not independent registration evidence. Explicit visually justified overrides take precedence over the overlap heuristic. Every decision, override and source SHA256 is recorded in dataset_manifest.json.', '',
             '| Patient | Slices | Pixel spacing mm | z spacing mm | Forward overlap | Reversed overlap | GT flipped |',
             '|---|---:|---|---|---:|---:|---|']
    for e in entries:
        dz = e['z_spacing_mm']
        lines.append(f'| {e["patient"]} | {e["slices"]} | {e["pixel_spacing_mm"]} | {min(dz):.3f}–{max(dz):.3f} | {e["alignment_forward"]:.5f} | {e["alignment_reverse"]:.5f} | {e["gt_reversed"]} |')
    lines += ['', 'Alignment overrides: ' + json.dumps(overrides), '', 'Actual slice counts and spacings above take precedence over the estimates in the supplied plan.', '', 'Pooled GT liver HU: ' + json.dumps(stats['pooled']), '', 'Physical volumes use pixel area × midpoint slice extents; z spacing rather than SliceThickness determines voxel extent.']
    (out / '00_dataset_audit.md').write_text('\n'.join(lines) + '\n')
    return entries


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA)
    parser.add_argument('--out', default='reports')
    args = parser.parse_args()
    audit(args.data, args.out)
