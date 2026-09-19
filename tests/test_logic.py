"""
test_logic.py -- Otomatik Birim Testleri (Teslimat 3)

Mevcut kritik matematiksel ve lojik fonksiyonlari (mapping, smoothing, dead zone, gesture)
webcam'den bagimsiz olarak test eder.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../src'))

from hand_state import HandState, FingerState
from motion_mapper import MotionMapper, FingerCalibration
from smoother import BionicHandSmoother
from bionic_hand_state import BionicHandState, BionicFingerTarget
from gesture_detector import GestureDetector, GestureType
from config import NEUTRAL_POSITION

class FakeLandmark:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class TestMotionEngine(unittest.TestCase):

    def test_motion_mapper(self):
        mapper = MotionMapper()
        state = HandState()
        state.hand_detected = True
        state.thumb.normalized = 0.5
        state.index.normalized = 0.8
        
        # Standart birebir esleme
        bionic = mapper.map(state)
        self.assertAlmostEqual(bionic.thumb.raw, 0.5)
        self.assertAlmostEqual(bionic.index.raw, 0.8)

        # Kalibre edilmis esleme
        # Input: 0.2 - 0.8, Output: 0.0 - 1.0
        calib = FingerCalibration(input_min=0.2, input_max=0.8, output_min=0.0, output_max=1.0)
        mapper.set_calibration("thumb", calib)
        bionic_calib = mapper.map(state)
        # (0.5 - 0.2) / (0.8 - 0.2) = 0.3 / 0.6 = 0.5
        self.assertAlmostEqual(bionic_calib.thumb.raw, 0.5)
        
        state.thumb.normalized = 0.8
        bionic_calib2 = mapper.map(state)
        self.assertAlmostEqual(bionic_calib2.thumb.raw, 1.0)
        
        state.thumb.normalized = 0.1
        bionic_calib3 = mapper.map(state)
        self.assertAlmostEqual(bionic_calib3.thumb.raw, 0.0)

    def test_smoother_and_dead_zone(self):
        smoother = BionicHandSmoother(alpha=0.5, dead_zone=0.02)
        # Baslangic noktasi = NEUTRAL_POSITION (0.0)
        
        # Raw = 0.8
        raw_state = BionicHandState(hand_detected=True)
        raw_state.thumb.raw = 0.8
        
        # Adim 1: 0.5 * 0.8 + 0.5 * 0.0 = 0.40 (degisim: 0.4 > 0.02 dead_zone) -> is_moving = True
        s1 = smoother.smooth(raw_state)
        self.assertAlmostEqual(s1.thumb.target, 0.4)
        self.assertTrue(s1.thumb.is_moving)
        
        # Dead zone testi
        # Smoothed = 0.4, Raw = 0.41
        raw_state.thumb.raw = 0.41
        # Yeni EMA: 0.5 * 0.41 + 0.5 * 0.40 = 0.405
        # Fark: 0.405 - 0.4 = 0.005 < 0.02 -> Hareket etmemeli, 0.40 kalmali
        s2 = smoother.smooth(raw_state)
        self.assertAlmostEqual(s2.thumb.target, 0.4)
        self.assertFalse(s2.thumb.is_moving)

    def test_gesture_detector(self):
        detector = GestureDetector(stability_frames=2)
        state = HandState(hand_detected=True)
        
        # Baslangicta hepsi kapali -> FIST
        for attr in ['thumb', 'index', 'middle', 'ring', 'pinky']:
            getattr(state, attr).is_open = False
            
        g1 = detector.update(state)
        self.assertEqual(g1, GestureType.UNKNOWN) # Henuz 2 frame dolmadi
        g2 = detector.update(state)
        self.assertEqual(g2, GestureType.FIST)    # 2. frame ayni
        
        # Sadece isaret parmagi acik -> POINT
        state.index.is_open = True
        g3 = detector.update(state)
        self.assertEqual(g3, GestureType.FIST) # Hala fist gozukuyor cunku history tam POINT degil
        g4 = detector.update(state)
        self.assertEqual(g4, GestureType.POINT) # Simdi POINT oldu
        
        # Isaret ve orta acik -> PEACE
        state.middle.is_open = True
        detector.update(state)
        g_peace = detector.update(state)
        self.assertEqual(g_peace, GestureType.PEACE)
        
        # Hepsi acik -> OPEN_HAND
        state.thumb.is_open = True
        state.ring.is_open = True
        state.pinky.is_open = True
        detector.update(state)
        g_open = detector.update(state)
        self.assertEqual(g_open, GestureType.OPEN_HAND)

        # Basparmak tek acik -> THUMBS_UP
        for attr in ['index', 'middle', 'ring', 'pinky']:
            getattr(state, attr).is_open = False
        detector.update(state)
        g_thumbs = detector.update(state)
        self.assertEqual(g_thumbs, GestureType.THUMBS_UP)
        
        # PINCH Test (isaret ve basparmak uclari yakin)
        # Mesafenin cok yakin oldugu bir senaryo
        # LMs dizisi gerekiyor (21 adet FakeLandmark)
        state.landmarks = [FakeLandmark(0,0,0) for _ in range(21)]
        state.landmarks[4] = FakeLandmark(0.5, 0.5, 0)  # Thumb tip
        state.landmarks[8] = FakeLandmark(0.51, 0.51, 0) # Index tip
        
        detector.update(state)
        g_pinch = detector.update(state)
        self.assertEqual(g_pinch, GestureType.PINCH)


if __name__ == '__main__':
    unittest.main()
