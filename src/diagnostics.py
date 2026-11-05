"""Dataset HU histogram and evidence for the recorded mask-alignment decision."""
import os
import tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'liver-hu-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json


def run(reports='reports'):
    reports = Path(reports)
    out = reports/'dataset_visualization'
    out.mkdir(exist_ok=True)
    manifest = json.loads((reports/'dataset_manifest.json').read_text())
    bins = np.linspace(-200, 400, 121)
    liver, other = np.zeros(120), np.zeros(120)
    for meta in manifest:
        pid = meta['patient']
        hu = np.load(reports/f'cache/{pid}_hu.npy', mmap_mode='r')
        gt = np.load(reports/f'cache/{pid}_gt.npy', mmap_mode='r')
        for image, mask in zip(hu, gt):
            liver += np.histogram(image[mask], bins)[0]
            other += np.histogram(image[(image > -500) & ~mask], bins)[0]
    centers = (bins[:-1]+bins[1:])/2
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(centers, liver/liver.sum(), label='Ground-truth liver')
    ax.plot(centers, other/other.sum(), label='Non-liver with raw HU > −500')
    ax.axvspan(50, 200, alpha=.12, color='green', label='Segmentation band: 50–200 HU')
    ax.set(xlabel='Raw CT HU', ylabel='Probability per 5-HU bin within shown range',
           title='CT dataset: liver and non-liver intensity overlap')
    ax.legend()
    fig.tight_layout()
    fig.savefig(out/'hu_histogram.png', dpi=150)
    plt.close(fig)
    (out/'README.md').write_text('Histogram uses raw HU, not windowed display pixels. The non-liver HU > -500 condition is a simple body proxy, not an anatomical body mask. Curves are normalized within the displayed -200 to 400 HU range. Visualization settings do not alter segmentation.\n')
    alignment_sensitivity(reports)
    print('Dataset visualization complete', flush=True)


def alignment_sensitivity(reports='reports'):
    """Show the two possible mask orders for cases needing visual review."""
    reports = Path(reports)
    out = reports/'figures'
    out.mkdir(exist_ok=True)
    manifest = json.loads((reports/'dataset_manifest.json').read_text())
    for meta in manifest:
        if not meta.get('heuristic_gt_reversed', False):
            continue
        pid = meta['patient']
        hu = np.load(reports/f'cache/{pid}_hu.npy', mmap_mode='r')
        gt = np.load(reports/f'cache/{pid}_gt.npy', mmap_mode='r')
        forward = gt[::-1] if meta['gt_reversed'] else gt
        indices = np.linspace(15, len(gt)-15, 5).astype(int)
        fig, axes = plt.subplots(2, 5, figsize=(15, 6))
        for col, index in enumerate(indices):
            for row, masks in enumerate([forward, forward[::-1]]):
                ax = axes[row, col]
                ax.imshow(hu[index], cmap='gray', vmin=-100, vmax=300)
                if masks[index].any():
                    ax.contour(masks[index], levels=[.5], colors='lime', linewidths=1)
                ax.set_title(f'{"Forward" if row==0 else "Reversed"} GT; slice {index}')
                ax.axis('off')
        fig.suptitle(f'CT {pid}: alignment review (green = ground truth)')
        fig.tight_layout()
        fig.savefig(out/f'alignment_CT_{pid}.png', dpi=110)
        plt.close(fig)


if __name__ == '__main__':
    run()
