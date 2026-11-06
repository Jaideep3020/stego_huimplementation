import unittest
import numpy as np
from scipy import ndimage as ndi
from pydicom.dataset import Dataset
from src.pipeline import hu_from_dicom, largest_component, morph, segment_slice


class PipelineTests(unittest.TestCase):
    def test_hu_conversion(self):
        d = Dataset()
        d.Modality='CT'; d.Rows=2; d.Columns=2; d.SamplesPerPixel=1
        d.PhotometricInterpretation='MONOCHROME2'; d.BitsAllocated=16
        d.BitsStored=16; d.HighBit=15; d.PixelRepresentation=0
        from pydicom.uid import ExplicitVRLittleEndian
        d.file_meta=Dataset(); d.file_meta.TransferSyntaxUID=ExplicitVRLittleEndian
        d.PixelData=np.array([[0,1],[100,500]],np.uint16).tobytes()
        d.RescaleSlope=2; d.RescaleIntercept=-1000
        np.testing.assert_array_equal(hu_from_dicom(d),[[-1000,-998],[-800,0]])
        del d.RescaleIntercept
        with self.assertRaises(ValueError): hu_from_dicom(d)

    def test_connectivity_and_largest(self):
        m=np.zeros((20,20),bool); m[1:4,1:4]=1; m[12:14,12:14]=1
        for c in (1,2):
            self.assertEqual(largest_component(m,c).sum(),9)
        m=np.eye(5,dtype=bool)
        self.assertEqual(largest_component(m,1).sum(),1)
        self.assertEqual(largest_component(m,2).sum(),5)
        self.assertFalse(largest_component(np.zeros_like(m)).any())

    def test_backends_equal(self):
        rng=np.random.default_rng(42)
        for shape in ('disk','square'):
            for c in (1,2):
                for order in ('fig1','fig3'):
                    # Dense foreground and edge objects exercise border and tie cases.
                    hu=rng.integers(-100,250,(51,53)).astype(np.float32)
                    for k in (1,3,5,7,9):
                        params=dict(med_k=1,open_k=k,close_k=k,shape=shape,connectivity=c,order=order)
                        np.testing.assert_array_equal(segment_slice(hu,**params),segment_slice(hu,**params,backend='opencv'))
        for _ in range(10):
            m=rng.random((30,32))>.55
            for c in (1,2):
                np.testing.assert_array_equal(largest_component(m,c),largest_component(m,c,'opencv'))

    def test_slice_independence(self):
        from src.pipeline import segment_volume
        a=np.zeros((2,21,21)); a[0,5:15,5:15]=100
        p=segment_volume(a,med_k=1,open_k=1,close_k=1)
        self.assertEqual(p[0].sum(),100); self.assertEqual(p[1].sum(),0)

    def test_invalid_config(self):
        for kw in [dict(tmin=201,tmax=200),dict(med_k=4),dict(order='bad'),dict(connectivity=3)]:
            with self.assertRaises(ValueError): segment_slice(np.zeros((20,20)),**kw)

    def test_threshold_endpoints(self):
        hu=np.array([[39,40,180,181]],np.float32)
        p=segment_slice(hu,med_k=1,open_k=1,close_k=1,use_lcc=False)
        np.testing.assert_array_equal(p,[[False,True,True,False]])

    def test_operation_orders(self):
        hu=np.zeros((40,50),np.float32)
        hu[5:17,5:17]=100
        hu[7:15,28:36]=100
        hu[10,17:28]=100
        p3=segment_slice(hu,med_k=1,open_k=3,close_k=1,order='fig3')
        p1=segment_slice(hu,med_k=1,open_k=3,close_k=1,order='fig1')
        self.assertGreater(p1.sum(),p3.sum())
        self.assertFalse(p3[:,28:].any())
        self.assertTrue(p1[:,28:].any())
