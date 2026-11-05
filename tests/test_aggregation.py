import unittest
import numpy as np
import pandas as pd
from src.metrics import from_confusion
from src.run_experiment import aggregate


class AggregationTests(unittest.TestCase):
    def test_patient_slice_and_micro_weights(self):
        rows=[]
        # Patient A: one perfect slice. B: two failed slices. Patient and slice weights differ.
        for patient,c in [('A',(10,0,0,90)),('B',(0,0,10,90)),('B',(0,0,10,90))]:
            rows.append(dict(patient=patient,gt_voxels=10,tp=c[0],fp=c[1],fn=c[2],tn=c[3],**from_confusion(*c)))
        ps=pd.DataFrame(rows)
        pp=[]
        for pid,t in ps.groupby('patient'):
            c=t[['tp','fp','fn','tn']].sum().to_numpy()
            pp.append(dict(patient=pid,tp=c[0],fp=c[1],fn=c[2],tn=c[3],**from_confusion(*c)))
        out=aggregate(pd.DataFrame(pp),ps)
        self.assertEqual(out['C1']['dice']['mean'],.5)
        self.assertAlmostEqual(out['C2']['dice']['mean'],1/3)
        self.assertEqual(out['C4']['dice'],.5)
        self.assertEqual(out['C1']['dice']['n'],2)
