"""Slice-wise reference pipeline with an equivalent optional OpenCV backend.

Adapted with borrowed P1 parameters:
  - tmin: 40 HU, tmax: 180 HU (pixel threshold)
  - med_k: 0 (disabled)
  - open_k: 0 (disabled)
  - close_k: 7 (disk radius 3)
  - connectivity: 2 (8-connected)
  - shape: disk
  - use_lcc: true

Execution order:
  HU conversion -> pixel threshold [40, 180] -> largest eight-connected component
  -> disk-radius-3 closing.
"""
import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import disk
from .io_chaos import hu_from_dicom


def validate_config(cfg):
    if cfg.get('tmin', 40) > cfg.get('tmax', 180):
        raise ValueError('tmin must not exceed tmax')
    for name in ('med_k', 'open_k', 'close_k'):
        k = cfg.get(name, {'med_k': 0, 'open_k': 0, 'close_k': 7}[name])
        if not isinstance(k, int) or k < 0 or (k > 1 and k % 2 == 0):
            raise ValueError(f'{name} must be 0, 1 or a positive odd integer')
    if cfg.get('order', 'fig3') not in ('fig3', 'fig1'):
        raise ValueError('Unknown operation order')
    if cfg.get('connectivity', 2) not in (1, 2):
        raise ValueError('Connectivity must be 1 (4-neighbour) or 2 (8-neighbour)')
    if cfg.get('shape', 'disk') not in ('disk', 'square'):
        raise ValueError('Unknown structuring element')


def largest_component(mask, connectivity=2, backend='scipy'):
    """Extract the largest connected component from a binary mask.
    
    Parameters:
      mask: 2D boolean ndarray.
      connectivity: 1 (4-neighbour) or 2 (8-neighbour).
      backend: 'scipy' or 'opencv'.
    """
    if backend == 'opencv':
        import cv2
        n, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask.astype(np.uint8),
            connectivity=4 if connectivity == 1 else 8,
            ltype=cv2.CV_32S
        )
        if n == 1:
            return np.zeros(mask.shape, bool)
        sizes = stats[1:, cv2.CC_STAT_AREA]
        candidates = np.flatnonzero(sizes == sizes.max()) + 1
        # scipy labels ties in raster order; enforce the same rule for OpenCV.
        winner = min(candidates, key=lambda k: int(np.flatnonzero(labels == k)[0])) if len(candidates) > 1 else candidates[0]
        return labels == winner

    labels, n = ndi.label(mask, structure=ndi.generate_binary_structure(2, connectivity))
    if n == 0:
        return np.zeros(mask.shape, bool)
    sizes = np.bincount(labels.ravel(), minlength=n + 1)
    sizes[0] = 0
    return labels == int(np.argmax(sizes))


def element(k, shape='disk'):
    return disk(k // 2).astype(bool) if shape == 'disk' else np.ones((k, k), bool)


def morph(mask, k, operation, shape='disk', backend='scipy'):
    if k <= 1:
        return mask
    se = element(k, shape)
    if backend == 'opencv':
        import cv2
        op = cv2.MORPH_OPEN if operation == 'open' else cv2.MORPH_CLOSE
        return cv2.morphologyEx(mask.astype(np.uint8), op, se.astype(np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0).astype(bool)
    fn = ndi.binary_opening if operation == 'open' else ndi.binary_closing
    return fn(mask, structure=se, border_value=0)


def stages(hu, tmin=40, tmax=180, med_k=0, open_k=0, close_k=7,
           order='fig3', connectivity=2, shape='disk', use_lcc=True,
           backend='scipy', prefiltered=False):
    """Return each 2D stage from an HU image, using the configured operation order.

    Order:
      HU conversion -> pixel threshold [tmin, tmax] -> largest connected component
      -> morphological closing.
    When open_k > 1, opening is applied according to `order` (before LCC in fig3,
    after LCC in fig1).
    """
    validate_config(dict(tmin=tmin, tmax=tmax, med_k=med_k, open_k=open_k, close_k=close_k,
                         order=order, connectivity=connectivity, shape=shape))
    x = hu if prefiltered or med_k <= 1 else ndi.median_filter(hu, size=med_k, mode='reflect')
    threshold = (x >= tmin) & (x <= tmax)
    if order == 'fig3':
        opened = morph(threshold, open_k, 'open', shape, backend) if open_k > 1 else threshold
        lcc = largest_component(opened, connectivity, backend) if use_lcc else opened
        before_close = lcc
    else:
        lcc = largest_component(threshold, connectivity, backend) if use_lcc else threshold
        opened = morph(lcc, open_k, 'open', shape, backend) if open_k > 1 else lcc
        before_close = opened
    final = morph(before_close, close_k, 'close', shape, backend)
    return dict(filtered=x, threshold=threshold, opening=opened, largest_cc=lcc, final=final)


def segment_slice(hu: np.ndarray, **kw) -> np.ndarray:
    """Segment one single-channel axial CT slice; output dtype is boolean."""
    return stages(hu, **kw)['final']


def segment_volume(hu_vol: np.ndarray, **kw) -> np.ndarray:
    """Stack independent slice predictions; performs no 3D post-processing."""
    if hu_vol.ndim != 3 or len(hu_vol) == 0:
        raise ValueError('Expected a non-empty (slices, rows, columns) HU volume')
    return np.stack([segment_slice(s, **kw) for s in hu_vol])
