"""Paper Fig. 3 stage layout, chosen by a recorded representative-case rule."""
import os
import tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'liver-hu-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json
import pandas as pd
import yaml
from .pipeline import stages


def fig3(reports='reports'):
    reports = Path(reports)
    out = reports / 'figures'
    out.mkdir(exist_ok=True)
    pp = pd.read_csv(reports / 'paper_protocol/per_patient.csv', dtype={'patient':str})
    # Lower median patient Dice, no choice based on visual appearance.
    pid = pp.sort_values(['dice','patient']).iloc[(len(pp)-1)//2].patient
    hu = np.load(reports / f'cache/{pid}_hu.npy', mmap_mode='r')
    gt = np.load(reports / f'cache/{pid}_gt.npy', mmap_mode='r')
    positive = np.flatnonzero(gt.reshape(len(gt),-1).any(axis=1))
    indices = positive[np.rint(np.linspace(0,len(positive)-1,5)).astype(int)]
    cfg = yaml.safe_load(Path('configs/paper_protocol.yaml').read_text())['pipeline']
    fig, axes = plt.subplots(6,5,figsize=(13,15))
    labels = ['(a) CT (−100 to 300 HU)','(b) Ground truth','(c) Threshold','(d) Opening','(e) Largest component','(f) Closing']
    for col, idx in enumerate(indices):
        s = stages(hu[idx], **cfg)
        images = [hu[idx],gt[idx],s['threshold'],s['opening'],s['largest_cc'],s['final']]
        for row,image in enumerate(images):
            ax=axes[row,col]
            ax.imshow(image,cmap='gray',vmin=-100 if row==0 else 0,vmax=300 if row==0 else 1)
            ax.set_xticks([]); ax.set_yticks([])
            if col==0: ax.set_ylabel(labels[row],fontsize=10)
            if row==0: ax.set_title(f'CT {pid}, slice {idx}')
    fig.suptitle('Fixed 50–200 HU protocol: five slices spanning the liver\nCase selected by median per-patient Dice',fontsize=15)
    fig.tight_layout(rect=(0,0,1,.96))
    fig.savefig(out / 'fig3_replica.png',dpi=130)
    plt.close(fig)
    (out / 'fig3_selection.json').write_text(json.dumps(dict(patient=pid,slices=indices.tolist(),rule='Lower median patient Dice; five equally spaced GT-positive indices'),indent=2))


if __name__ == '__main__':
    fig3()
