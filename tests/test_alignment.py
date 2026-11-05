import json
from pathlib import Path
import unittest
import numpy as np
from src.io_chaos import natural_key


class AlignmentTests(unittest.TestCase):
    def test_numeric_gt_sorting(self):
        self.assertEqual(sorted(['liver_GT_10.png','liver_GT_2.png'],key=natural_key),['liver_GT_2.png','liver_GT_10.png'])

    def test_real_audited_cases(self):
        path=Path('reports/dataset_manifest.json')
        if not path.exists(): self.skipTest('Run dataset audit first')
        manifest=json.loads(path.read_text())
        if any(not Path(f'reports/cache/{m["patient"]}_{kind}.npy').exists()
               for m in manifest for kind in ('hu', 'gt')):
            self.skipTest('Run the CT audit first to enable real-dataset integration checks')
        self.assertEqual(len(manifest),20)
        for m in manifest:
            hu=np.load(f'reports/cache/{m["patient"]}_hu.npy',mmap_mode='r')
            gt=np.load(f'reports/cache/{m["patient"]}_gt.npy',mmap_mode='r')
            self.assertEqual(hu.shape,gt.shape)
            self.assertEqual(int(gt.sum()),m['gt_voxels'])
            self.assertEqual(gt.dtype,np.dtype(bool))
            if m.get('alignment_override'):
                self.assertTrue(m['alignment_override']['reason'])
                self.assertEqual(m['gt_reversed'],m['alignment_override']['order']=='reversed')
            else:
                self.assertEqual(m['gt_reversed'],m['alignment_reverse']>m['alignment_forward']+1e-12)
            self.assertEqual(len(m['dicom_files']),len(m['gt_files']))
