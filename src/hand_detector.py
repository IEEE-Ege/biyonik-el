"""
hand_detector.py -- MediaPipe el algılama modülü (Tasks API)

MediaPipe 1.0+ Tasks API kullanır: mediapipe.tasks.vision.HandLandmarker
Model dosyası: models/hand_landmarker.task

HandLandmarker VIDEO modunda çalışır — her frame için timestamp gerektirir.
"""

import os
import time
import cv2
import numpy as np
import mediapipe as mp

from hand_state import HandState
from finger_state import compute_all_fingers

# Tasks API bileşenleri
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarksConnections = mp.tasks.vision.HandLandmarksConnections
RunningMode = mp.tasks.vision.RunningMode

# Çizim araçları
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

# MediaPipe'ın döndürdüğü handedness'ı Türkçeye çevir
_HANDEDNESS_MAP = {
    "Left": "Sol",
    "Right": "Sag",
}

# Model dosyası yolu (bu dosyadan iki dizin yukarı)
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "hand_landmarker.task",
)


class HandDetector:
    """
    MediaPipe HandLandmarker sarmalayıcısı (Tasks API 1.0+).

    VIDEO modunda çalışır — gerçek zamanlı webcam akışı için optimize edilmiş.
    """

    def __init__(
        self,
        model_path: str = _MODEL_PATH,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.6,
        min_presence_confidence: float = 0.5,
    ):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"HandLandmarker model dosyası bulunamadı: {model_path}\n"
                "Lütfen models/hand_landmarker.task dosyasını indirin."
            )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._state = HandState()
        self._last_result = None  # Son algılama sonucu (çizim için)
        self._start_time_ms = int(time.time() * 1000)

    def process(self, frame: np.ndarray) -> HandState:
        """
        BGR frame'i işle ve HandState döndür.

        Args:
            frame: OpenCV BGR formatında kamera frame'i

        Returns:
            Güncellenmiş HandState
        """
        # BGR → RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # MediaPipe Image objesi oluştur
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # VIDEO modunda timestamp gerekiyor (milisaniye)
        timestamp_ms = int(time.time() * 1000) - self._start_time_ms

        # El landmark tespiti
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        self._last_result = result

        self._state.reset()

        if not result.hand_landmarks or len(result.hand_landmarks) == 0:
            return self._state

        # İlk eli al
        landmarks = result.hand_landmarks[0]

        # Handedness
        handedness_label = "Right"
        if result.handedness and len(result.handedness) > 0:
            handedness_label = result.handedness[0][0].category_name

        handedness_tr = _HANDEDNESS_MAP.get(handedness_label, handedness_label)

        # Landmark listesi (NormalizedLandmark objeleri — x, y, z alanları var)
        lms = landmarks  # 21 NormalizedLandmark

        # Parmak durumlarını hesapla
        fingers = compute_all_fingers(lms, handedness_tr)

        # Bilek piksel koordinatı
        h, w = frame.shape[:2]
        wrist = lms[0]
        wrist_px = (int(wrist.x * w), int(wrist.y * h))

        # HandState'i doldur
        self._state.hand_detected = True
        self._state.handedness = handedness_tr
        self._state.thumb = fingers["thumb"]
        self._state.index = fingers["index"]
        self._state.middle = fingers["middle"]
        self._state.ring = fingers["ring"]
        self._state.pinky = fingers["pinky"]
        self._state.landmarks = lms
        self._state.wrist_pos = wrist_px

        return self._state

    def draw_landmarks(self, frame: np.ndarray, state: HandState) -> np.ndarray:
        """
        Landmark noktalarını ve bağlantı çizgilerini frame üzerine çizer.
        Kendi OpenCV implementasyonumuzu kullanıyoruz (Tasks API bağımlılığı yok).
        """
        if not state.hand_detected or not state.landmarks:
            return frame

        h, w = frame.shape[:2]
        lms = state.landmarks

        # Bağlantı çiftleri (MediaPipe el şeması)
        connections = [
            (0,1),(1,2),(2,3),(3,4),        # Başparmak
            (0,5),(5,6),(6,7),(7,8),         # İşaret
            (9,10),(10,11),(11,12),          # Orta
            (13,14),(14,15),(15,16),         # Yüzük
            (0,17),(17,18),(18,19),(19,20),  # Serçe
            (5,9),(9,13),(13,17),            # Avuç içi
            (0,5),(5,9),(9,13),(13,17),      # Avuç içi yatay
        ]

        # Bağlantı çizgileri
        for start_idx, end_idx in connections:
            p1 = lms[start_idx]
            p2 = lms[end_idx]
            x1, y1 = int(p1.x * w), int(p1.y * h)
            x2, y2 = int(p2.x * w), int(p2.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), (200, 200, 200), 2, cv2.LINE_AA)

        # Landmark noktaları
        for i, lm in enumerate(lms):
            px, py = int(lm.x * w), int(lm.y * h)
            # Parmak uçlarını farklı renkle göster (4,8,12,16,20)
            if i in (4, 8, 12, 16, 20):
                cv2.circle(frame, (px, py), 7, (0, 255, 100), -1, cv2.LINE_AA)
                cv2.circle(frame, (px, py), 7, (255, 255, 255), 1, cv2.LINE_AA)
            elif i == 0:  # Bilek
                cv2.circle(frame, (px, py), 6, (100, 100, 255), -1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (px, py), 4, (255, 100, 100), -1, cv2.LINE_AA)

        return frame

    def close(self):
        """MediaPipe kaynaklarını serbest bırak."""
        if self._landmarker:
            self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

