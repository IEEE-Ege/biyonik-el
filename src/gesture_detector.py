"""
gesture_detector.py -- Gesture Recognition Module

Mevcut parmak açıklık durumlarına ve landmark koordinatlarına bakarak
temel el hareketlerini (gesture) tespit eder.
"""

import numpy as np
from collections import deque
from hand_state import HandState
import config as cfg

class GestureType:
    UNKNOWN = "UNKNOWN"
    OPEN_HAND = "OPEN_HAND"
    FIST = "FIST"
    POINT = "POINT"
    PEACE = "PEACE"
    THUMBS_UP = "THUMBS_UP"
    PINCH = "PINCH"

class GestureDetector:
    def __init__(self, stability_frames: int = cfg.GESTURE_STABILITY_FRAMES):
        self.stability_frames = stability_frames
        self.history = deque(maxlen=stability_frames)
        self.current_gesture = GestureType.UNKNOWN

    def _calculate_pinch_distance(self, lms: list) -> float:
        """Başparmak ucu ve işaret parmağı ucu arasındaki 3D mesafeyi hesaplar."""
        if not lms or len(lms) < 21:
            return 1.0
        thumb_tip = np.array([lms[4].x, lms[4].y, lms[4].z])
        index_tip = np.array([lms[8].x, lms[8].y, lms[8].z])
        return float(np.linalg.norm(thumb_tip - index_tip))

    def _detect_raw_gesture(self, state: HandState) -> str:
        """Tek bir frame için gesture tespiti yapar."""
        if not state.hand_detected:
            return GestureType.UNKNOWN

        t_open = state.thumb.is_open
        i_open = state.index.is_open
        m_open = state.middle.is_open
        r_open = state.ring.is_open
        p_open = state.pinky.is_open

        open_fingers = sum([t_open, i_open, m_open, r_open, p_open])

        # Pinch tespiti (Başparmak ve İşaret ucu birbirine çok yakınsa, diğerleri kapalı veya açıksa fark etmez, ama genelde kapalı olur. Pinch için sadece 2 parmak ucu mesafesi önemli)
        # Mesafeyi kontrol edelim
        pinch_dist = self._calculate_pinch_distance(state.landmarks)
        if pinch_dist < 0.05 and not m_open and not r_open and not p_open:
             return GestureType.PINCH

        if open_fingers == 5:
            return GestureType.OPEN_HAND
        
        if open_fingers == 0:
            return GestureType.FIST

        if i_open and not m_open and not r_open and not p_open:
            if not t_open:
                return GestureType.POINT
            # Bazen point yaparken başparmak da hafif açık kalabilir.
            # Point'te esas olan sadece işaret parmağının açık olmasıdır.
            
        if i_open and m_open and not r_open and not p_open:
            return GestureType.PEACE
            
        if t_open and not i_open and not m_open and not r_open and not p_open:
            return GestureType.THUMBS_UP

        return GestureType.UNKNOWN

    def update(self, state: HandState) -> str:
        """
        State'i alır, raw gesture hesaplar, temporal stability (debounce)
        uygular ve en güncel stabil gesture'ı döner.
        """
        raw_gesture = self._detect_raw_gesture(state)
        self.history.append(raw_gesture)

        # Eğer history tamamen aynı gesture'dan oluşuyorsa, current_gesture'ı güncelle
        if len(self.history) == self.stability_frames:
            if all(g == raw_gesture for g in self.history):
                self.current_gesture = raw_gesture

        # Eğer el kaybolursa hemen UNKNOWN yap
        if not state.hand_detected:
            self.history.clear()
            self.current_gesture = GestureType.UNKNOWN

        return self.current_gesture
