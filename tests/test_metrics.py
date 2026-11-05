import unittest
import numpy as np
from src.metrics import confusion, scores


class MetricsTests(unittest.TestCase):
    def test_known_overlap(self):
        p = np.array([1,1,0,0], bool)
        g = np.array([1,0,1,0], bool)
        s = scores(p,g)
        self.assertEqual(confusion(p,g), (1,1,1,1))
        self.assertEqual(s['dice'], .5)
        self.assertAlmostEqual(s['iou_liver'], 1/3)
        self.assertAlmostEqual(s['iou_bg'], 1/3)
        self.assertAlmostEqual(s['miou'], 1/3)

    def test_identical_disjoint_and_empty(self):
        a = np.eye(16, dtype=bool)
        self.assertEqual(scores(a,a)['dice'], 1)
        self.assertEqual(scores(a,a)['miou'], 1)
        self.assertEqual(scores(a,~a)['dice'], 0)
        z = np.zeros_like(a)
        self.assertEqual(scores(z,z)['dice'], 1)
        self.assertEqual(scores(z,z)['miou'], 1)

    def test_shape_mismatch(self):
        with self.assertRaises(ValueError):
            confusion(np.zeros((3,4)), np.zeros((4,3)))
