"""
bionic_visualizer.py -- 2D Biyonik El Görselleştirici

İki bileşen içerir:

1. BionicPanel — Kamera frame üzerine progress bar paneli çizer
   Her parmak için: ham değer, smoothed değer, servo açısı

2. BionicHand2D — Kamera frame üzerine basit 2D el şeması çizer
   BionicHandState'e göre parmaklar açılır/kapanır
"""

import math
import numpy as np
import cv2

from bionic_hand_state import BionicHandState
import config as cfg

# Renk paleti (BGR)
C_PANEL_BG     = (15, 15, 15)
C_WHITE        = (255, 255, 255)
C_GRAY         = (140, 140, 140)
C_CYAN         = (200, 180, 40)
C_GREEN        = (60, 200, 60)
C_ORANGE       = (40, 140, 220)
C_RED          = (60, 60, 210)
C_HAND_OUTLINE = (100, 200, 100)
C_HAND_JOINT   = (255, 255, 255)
C_HAND_TIP     = (40, 220, 40)
C_HAND_LOST    = (40, 40, 200)

FONT           = cv2.FONT_HERSHEY_SIMPLEX


def _draw_alpha_rect(img, x1, y1, x2, y2, color, alpha=0.75):
    """Yarı saydam dikdörtgen."""
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def _progress_bar(frame, x, y, w, h, value: float, raw: float = None):
    """
    Çift katmanlı progress bar:
      - Arka kısım: ham (raw) değer (ince, soluk)
      - Ön kısım: smoothed değer (tam, parlak)
    """
    # Arka plan
    cv2.rectangle(frame, (x, y), (x + w, y + h), (40, 40, 40), -1)

    # Ham değer (varsa, ince çizgi)
    if raw is not None:
        raw_w = int(raw * w)
        if raw_w > 0:
            cv2.rectangle(frame, (x, y + 2), (x + raw_w, y + h - 2), (60, 80, 60), -1)

    # Smoothed değer
    fill_w = int(value * w)
    if fill_w > 0:
        r = int(200 * (1 - value))
        g = int(160 * value + 50)
        cv2.rectangle(frame, (x, y), (x + fill_w, y + h), (30, g, r), -1)

    # Kenarlık
    cv2.rectangle(frame, (x, y), (x + w, y + h), (70, 70, 70), 1)


class BionicPanel:
    """
    Kamera frame üzerine biyonik el kontrol paneli çizer.

    Her parmak için:
      - İsim etiketi
      - Smoothed değer (progress bar)
      - Ham değer (arka plan bar)
      - Yüzde ve servo açısı
      - HAREKET EDİYOR göstergesi
    """

    FINGER_NAMES = [
        ("Basparmak", "thumb"),
        ("Isaret   ", "index"),
        ("Orta     ", "middle"),
        ("Yuzuk    ", "ring"),
        ("Serce    ", "pinky"),
    ]

    def __init__(self):
        self.panel_w = 360
        self.line_h  = 38
        self.bar_w   = 160
        self.bar_h   = 13
        self.pad     = 10

    def draw(self, frame: np.ndarray, state: BionicHandState) -> np.ndarray:
        h, w = frame.shape[:2]
        panel_h = len(self.FINGER_NAMES) * self.line_h + 60

        # Alt sol köşeye yerleştir
        px = self.pad
        py = h - panel_h - self.pad

        # Panel arka planı
        _draw_alpha_rect(frame, px, py, px + self.panel_w, py + panel_h,
                         C_PANEL_BG, alpha=0.80)

        x = px + self.pad
        y = py + self.pad + 16

        # Başlık
        title = "BIYONIK EL KONTROL PANELI"
        if state.hand_lost:
            title += " [EL KAYIP]"
        cv2.putText(frame, title, (x, y), FONT, 0.52, C_CYAN, 1)
        y += 20
        cv2.line(frame, (x, y), (px + self.panel_w - self.pad, y), (60, 60, 60), 1)
        y += 8

        # El yoksa rengi değiştir
        active = state.hand_detected or state.hand_lost

        for label, attr in self.FINGER_NAMES:
            finger = getattr(state, attr)
            sv  = finger.target
            raw = finger.raw
            ang = finger.servo_angle()

            # İsim
            cv2.putText(frame, label, (x, y), FONT, 0.45, C_WHITE, 1)

            # Progress bar
            bar_x = x + 90
            _progress_bar(frame, bar_x, y - 10, self.bar_w, self.bar_h, sv, raw)

            # Yüzde
            pct_text = f"{sv * 100:.0f}%"
            cv2.putText(frame, pct_text, (bar_x + self.bar_w + 6, y),
                        FONT, 0.42, C_GRAY, 1)

            # Servo açısı
            ang_text = f"{ang:3d}d"
            cv2.putText(frame, ang_text, (bar_x + self.bar_w + 40, y),
                        FONT, 0.42, C_GRAY, 1)

            # Hareket göstergesi
            if finger.is_moving:
                cv2.circle(frame, (px + self.panel_w - 15, y - 4), 4, C_GREEN, -1)

            y += self.line_h

        return frame


class BionicHand2D:
    """
    Basit 2D biyonik el çizici.

    BionicHandState.targets() değerlerine göre parmaklar açılır/kapanır.
    Değer 1.0 = tamamen açık (düz), 0.0 = tamamen kapalı (kıvrık).

    Geometri: Her parmak 3 segment. Her eklemdeki kıvrılma açısı
    closure_amount'a (1 - target) bağlı.
    """

    # Parmak tanımları: (x_ofset_palm, base_angle_deg, segment_lengths, max_curl_deg_per_joint)
    # x_ofset_palm: avuç merkezinden parmak kökü x ofseti (ölçekli)
    FINGER_DEFS = [
        # isim,     palm_x, palm_y, base_ang, segs,               max_curl
        ("Thumb",   -0.55,  0.05,   -50,      [0.30, 0.22, 0.18],  55),
        ("Index",   -0.28,  -0.10,  -4,       [0.35, 0.25, 0.20],  80),
        ("Middle",  -0.05,  -0.13,   0,       [0.38, 0.27, 0.22],  80),
        ("Ring",     0.18,  -0.10,   4,       [0.35, 0.25, 0.20],  80),
        ("Pinky",    0.38,   0.00,   8,       [0.25, 0.18, 0.15],  80),
    ]

    def __init__(self, origin_x: int, origin_y: int, scale: int):
        """
        Args:
            origin_x/y: Avuç merkezi piksel koordinatı
            scale: Piksel cinsinden el büyüklük faktörü (~90)
        """
        self.ox = origin_x
        self.oy = origin_y
        self.scale = scale

    def draw(self, frame: np.ndarray, state: BionicHandState) -> np.ndarray:
        targets = state.targets()  # [thumb, index, middle, ring, pinky]
        hand_ok = state.hand_detected or state.hand_lost

        # Avuç içi (yuvarlak dikdörtgen benzeri)
        palm_pts = np.array([
            [self.ox - int(0.50 * self.scale), self.oy],
            [self.ox + int(0.45 * self.scale), self.oy],
            [self.ox + int(0.45 * self.scale), self.oy + int(0.40 * self.scale)],
            [self.ox - int(0.50 * self.scale), self.oy + int(0.40 * self.scale)],
        ], dtype=np.int32)

        # Avuç dolgusu
        overlay = frame.copy()
        cv2.fillPoly(overlay, [palm_pts], (20, 40, 20))
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        cv2.polylines(frame, [palm_pts], True, C_HAND_OUTLINE, 1, cv2.LINE_AA)

        # Her parmağı çiz
        for i, (fname, px_ratio, py_ratio, base_ang, segs, max_curl) in enumerate(self.FINGER_DEFS):
            target = targets[i] if i < len(targets) else 0.0
            closure = target  # 0.0=açık, 1.0=kapalı (yeni mekanik semantik)

            # Parmak kök koordinatı
            rx = self.ox + int(px_ratio * self.scale)
            ry = self.oy + int(py_ratio * self.scale)

            # Her eklemdeki curl açısı
            joint_curl = closure * max_curl

            self._draw_finger(frame, rx, ry, base_ang, segs, joint_curl, target)

        # El kayıp uyarısı
        if state.hand_lost:
            cx = self.ox
            cy = self.oy + int(0.55 * self.scale)
            cv2.putText(frame, "EL YOK", (cx - 25, cy),
                        FONT, 0.40, C_HAND_LOST, 1)

        # Gesture
        if hasattr(self, 'current_gesture') and self.current_gesture:
            cv2.putText(frame, f"GESTURE: {self.current_gesture}", (self.ox - 40, self.oy - int(0.7 * self.scale)),
                        FONT, 0.5, C_CYAN, 1)

        return frame

    def set_gesture(self, gesture_name: str):
        self.current_gesture = gesture_name

    def _draw_finger(self, frame, start_x, start_y, base_angle_deg,
                     seg_ratios, joint_curl_deg, target):
        """Tek bir parmağı çiz."""
        x, y = float(start_x), float(start_y)
        angle_rad = math.radians(base_angle_deg - 90)  # Yukarı = -90°

        # Renk: target değerine göre kırmızı→yeşil
        r = int(200 * (1 - target))
        g = int(160 * target + 50)
        color = (30, g, r)

        points = [(int(x), int(y))]

        for seg_ratio in seg_ratios:
            seg_len = seg_ratio * self.scale
            nx = x + seg_len * math.cos(angle_rad)
            ny = y + seg_len * math.sin(angle_rad)
            points.append((int(nx), int(ny)))
            x, y = nx, ny
            # Sonraki segmentte kıvrılma uygula (eklem açısı)
            angle_rad += math.radians(joint_curl_deg)

        # Segment çizgileri
        for i in range(len(points) - 1):
            cv2.line(frame, points[i], points[i + 1], color, 3, cv2.LINE_AA)

        # Eklem noktaları
        for i, pt in enumerate(points[:-1]):
            cv2.circle(frame, pt, 4, C_HAND_JOINT, -1, cv2.LINE_AA)

        # Parmak ucu
        if points:
            cv2.circle(frame, points[-1], 5, C_HAND_TIP, -1, cv2.LINE_AA)
            cv2.circle(frame, points[-1], 5, C_WHITE, 1, cv2.LINE_AA)


class DiagnosticPanel:
    """
    Sisteme ait raw, smoothed, hedef değerleri ve performansı ekranda
    yazı olarak gösteren diagnostic (hata ayıklama) paneli.
    """
    def __init__(self):
        self.x = 20
        self.y = 20
        self.line_h = 20

    def draw(self, frame: np.ndarray, state, bionic, gesture: str, fps: float, is_logging: bool, controller: 'ControllerInterface'):
        h, w = frame.shape[:2]
        
        px = self.x
        py = self.y
        
        # Yarı saydam arkaplan
        _draw_alpha_rect(frame, px, py, px + 300, py + 410, C_PANEL_BG, alpha=0.6)
        
        y = py + 20
        
        cv2.putText(frame, "--- DIAGNOSTIC MODE ---", (px + 10, y), FONT, 0.5, C_CYAN, 1)
        y += self.line_h
        cv2.putText(frame, f"FPS: {fps:.1f}", (px + 10, y), FONT, 0.45, C_WHITE, 1)
        y += self.line_h
        cv2.putText(frame, f"LOGGING: {'AÇIK' if is_logging else 'KAPALI'}", (px + 10, y), FONT, 0.45, C_RED if is_logging else C_GRAY, 1)
        y += self.line_h
        
        # Controller Durumu
        mode_name = controller.get_mode_name()
        conn_str = "CONNECTED" if controller.is_connected() else "DISCONNECTED"
        conn_color = C_GREEN if controller.is_connected() else C_GRAY
        cv2.putText(frame, f"CTRL: {mode_name} [{conn_str}]", (px + 10, y), FONT, 0.45, conn_color, 1)
        y += self.line_h
        
        cv2.putText(frame, f"HAND: {'DETECTED' if state.hand_detected else 'LOST'} [{state.handedness}]", (px + 10, y), FONT, 0.45, C_GREEN if state.hand_detected else C_GRAY, 1)
        y += self.line_h
        cv2.putText(frame, f"GESTURE: {gesture}", (px + 10, y), FONT, 0.5, C_ORANGE, 1)
        y += self.line_h * 2
        
        cv2.putText(frame, "FINGER   RAW%   TARGET(DEG)", (px + 10, y), FONT, 0.45, C_CYAN, 1)
        y += self.line_h
        
        # controller.get_servo_angles() üzerinden anlık açıları da alabiliriz
        servo_angles = controller.get_servo_angles() if hasattr(controller, 'get_servo_angles') else {}
        
        fingers = [
            ("Thumb ", state.thumb.normalized, "Basparmak"),
            ("Index ", state.index.normalized, "Isaret"),
            ("Middle", state.middle.normalized, "Orta"),
            ("Ring  ", state.ring.normalized, "Yuzuk"),
            ("Pinky ", state.pinky.normalized, "Serce"),
        ]
        
        for name, r, key in fingers:
            if not state.hand_detected:
                r = 0.0
            
            # Açı
            angle = servo_angles.get(key, 0)
            
            # Yüzdelik RAW (0.0 = %0 = Açık, 1.0 = %100 = Kapalı)
            pct = int(r * 100)
            
            # Durum
            status = "KAPALI" if r > 0.6 else "ACIK  " if r < 0.4 else "ORTA  "
            
            text = f"{name}: {status} | {pct:3d}% | {angle:2d} deg"
            cv2.putText(frame, text, (px + 10, y), FONT, 0.45, C_WHITE, 1)
            y += self.line_h
            
        y += self.line_h
        cv2.putText(frame, "CONTROLS:", (px + 10, y), FONT, 0.45, C_CYAN, 1)
        y += int(self.line_h * 0.8)
        cv2.putText(frame, "[D] Diagnostic Aç/Kapat", (px + 10, y), FONT, 0.4, C_GRAY, 1)
        y += int(self.line_h * 0.8)
        cv2.putText(frame, "[L] Logging Aç/Kapat", (px + 10, y), FONT, 0.4, C_GRAY, 1)
        y += int(self.line_h * 0.8)
        cv2.putText(frame, "[R] Smoother Sifirla", (px + 10, y), FONT, 0.4, C_GRAY, 1)
        y += int(self.line_h * 0.8)
        cv2.putText(frame, "[A] Arduino Modu", (px + 10, y), FONT, 0.4, C_GRAY, 1)
        y += int(self.line_h * 0.8)
        cv2.putText(frame, "[S] Simulation Modu", (px + 10, y), FONT, 0.4, C_GRAY, 1)
        y += int(self.line_h * 0.8)
        cv2.putText(frame, "[ESC/Q] Cikis", (px + 10, y), FONT, 0.4, C_GRAY, 1)

        return frame

