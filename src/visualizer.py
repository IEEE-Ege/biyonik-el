"""
visualizer.py — Ekran üzeri görselleştirme modülü

HandState ve SimulationController verilerini OpenCV frame üzerine çizer.
Temiz, okunabilir bir HUD (heads-up display) oluşturur.
"""

import cv2
import numpy as np
from hand_state import HandState
from simulation import SimulationController

# ── Renk paleti (BGR) ────────────────────────────────────────────────────────
COLOR_BG_PANEL   = (20, 20, 20)       # Koyu arka plan
COLOR_TEXT_WHITE = (255, 255, 255)    # Beyaz metin
COLOR_TEXT_GREEN = (80, 220, 80)      # Yeşil (açık parmak)
COLOR_TEXT_RED   = (80, 80, 220)      # Kırmızı (kapalı parmak)
COLOR_TEXT_CYAN  = (220, 200, 60)     # Sarımsı (FPS, başlık)
COLOR_TEXT_GRAY  = (160, 160, 160)    # Gri (ikincil bilgi)
COLOR_BAR_FILL   = (60, 180, 60)      # Progress bar dolu
COLOR_BAR_EMPTY  = (50, 50, 50)       # Progress bar boş
COLOR_BORDER     = (80, 80, 80)       # Panel kenarlığı

# ── Yazı tipi ayarları ────────────────────────────────────────────────────────
FONT          = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_L  = 0.65
FONT_SCALE_S  = 0.50
FONT_THICK    = 1
FONT_THICK_B  = 2

# ── Panel boyutları ───────────────────────────────────────────────────────────
PANEL_W       = 340   # Sol panel genişliği
PADDING       = 12    # İç kenar boşluğu
LINE_H        = 26    # Satır yüksekliği
BAR_H         = 12    # Progress bar yüksekliği
BAR_W         = 140   # Progress bar genişliği


def _draw_rounded_rect(img, x1, y1, x2, y2, color, alpha=0.75):
    """Yarı saydam dikdörtgen çizer (panel arka planı için)."""
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def _draw_progress_bar(frame, x, y, value: float, width=BAR_W, height=BAR_H):
    """
    [0.0, 1.0] değerini yatay progress bar olarak çizer.
    """
    # Arka plan
    cv2.rectangle(frame, (x, y), (x + width, y + height), COLOR_BAR_EMPTY, -1)
    # Dolu kısım
    filled_w = int(value * width)
    if filled_w > 0:
        # Renk: 0 = kırmızı, 1 = yeşil (BGR)
        r = int(220 * (1 - value))
        g = int(180 * value + 60)
        b = 40
        cv2.rectangle(frame, (x, y), (x + filled_w, y + height), (b, g, r), -1)
    # Kenarlık
    cv2.rectangle(frame, (x, y), (x + width, y + height), COLOR_BORDER, 1)


class Visualizer:
    """
    HandState ve SimulationController verilerini ekrana çizen sınıf.
    """

    def __init__(self, show_sim_panel: bool = True):
        self.show_sim_panel = show_sim_panel

        # Parmak görüntü sırası ve etiketleri
        self.finger_labels = [
            ("Basparmak", "thumb"),
            ("Isaret   ", "index"),
            ("Orta     ", "middle"),
            ("Yuzuk    ", "ring"),
            ("Serce    ", "pinky"),
        ]

    def render(
        self,
        frame: np.ndarray,
        state: HandState,
        fps: float,
        sim: SimulationController | None = None,
    ) -> np.ndarray:
        """
        Tüm overlay'leri frame üzerine çizer.

        Args:
            frame: BGR kamera frame'i (landmark'lar zaten çizilmiş olabilir)
            state: Güncel HandState
            fps: Anlık FPS değeri
            sim: SimulationController (None ise sim paneli gösterilmez)

        Returns:
            Overlay'ler eklenmiş frame
        """
        h, w = frame.shape[:2]

        # Sol bilgi paneli
        self._draw_info_panel(frame, state, fps, w, h)

        # Simülasyon paneli (sağ üst köşe)
        if self.show_sim_panel and sim is not None:
            self._draw_sim_panel(frame, sim, state, w, h)

        # El bulunamadı uyarısı
        if not state.hand_detected:
            self._draw_no_hand_warning(frame, w, h)

        return frame

    def _draw_info_panel(self, frame, state: HandState, fps: float, w, h):
        """Sol bilgi panelini çiz."""
        panel_h = 330
        panel_x = 10
        panel_y = 10

        # Panel arka planı
        _draw_rounded_rect(frame, panel_x, panel_y,
                           panel_x + PANEL_W, panel_y + panel_h,
                           COLOR_BG_PANEL, alpha=0.78)

        x = panel_x + PADDING
        y = panel_y + PADDING + 16

        # ── Başlık ───────────────────────────────────────────────────────────
        cv2.putText(frame, "BIYONIK EL — El Analizi", (x, y),
                    FONT, FONT_SCALE_L, COLOR_TEXT_CYAN, FONT_THICK_B)
        y += LINE_H

        # Ayırıcı çizgi
        cv2.line(frame, (x, y), (panel_x + PANEL_W - PADDING, y), COLOR_BORDER, 1)
        y += LINE_H - 6

        # ── FPS ──────────────────────────────────────────────────────────────
        fps_color = COLOR_TEXT_GREEN if fps >= 20 else COLOR_TEXT_RED
        cv2.putText(frame, f"FPS: {fps:.1f}", (x, y),
                    FONT, FONT_SCALE_S, fps_color, FONT_THICK)
        y += LINE_H

        # ── El tespit durumu ─────────────────────────────────────────────────
        if state.hand_detected:
            det_text = f"El: TESPIT EDILDI  [{state.handedness}]"
            det_color = COLOR_TEXT_GREEN
        else:
            det_text = "El: TESPIT EDILEMEDI"
            det_color = COLOR_TEXT_RED

        cv2.putText(frame, det_text, (x, y),
                    FONT, FONT_SCALE_S, det_color, FONT_THICK)
        y += LINE_H + 4

        # Ayırıcı
        cv2.line(frame, (x, y - 4), (panel_x + PANEL_W - PADDING, y - 4), COLOR_BORDER, 1)

        # ── Parmak durumları ─────────────────────────────────────────────────
        for label, attr in self.finger_labels:
            finger = getattr(state, attr)
            durum = "ACIK" if finger.is_open else "KAPALI"
            color = COLOR_TEXT_GREEN if finger.is_open else COLOR_TEXT_RED

            # İsim + durum
            cv2.putText(frame, f"{label}: {durum}", (x, y),
                        FONT, FONT_SCALE_S, color, FONT_THICK)

            # Açı değeri (sağ tarafta)
            angle_text = f"{finger.angle_deg:.0f}°"
            cv2.putText(frame, angle_text, (x + 195, y),
                        FONT, FONT_SCALE_S, COLOR_TEXT_GRAY, FONT_THICK)
            y += 18

            # Progress bar (normalize değer)
            _draw_progress_bar(frame, x, y, finger.normalized)
            # Yüzde değeri
            pct_text = f"{finger.normalized * 100:.0f}%"
            cv2.putText(frame, pct_text, (x + BAR_W + 6, y + BAR_H - 2),
                        FONT, 0.42, COLOR_TEXT_GRAY, 1)
            y += BAR_H + 8

    def _draw_sim_panel(self, frame, sim: SimulationController, state: HandState, w, h):
        """Sağ üst köşede simülasyon/servo panelini çiz."""
        finger_names = SimulationController.FINGER_NAMES
        data = sim.get_display_data()
        angles = sim.get_servo_angles()

        panel_w = 280
        panel_h = len(finger_names) * 38 + 55
        panel_x = w - panel_w - 10
        panel_y = 10

        _draw_rounded_rect(frame, panel_x, panel_y,
                           panel_x + panel_w, panel_y + panel_h,
                           COLOR_BG_PANEL, alpha=0.78)

        x = panel_x + PADDING
        y = panel_y + PADDING + 16

        # Başlık
        cv2.putText(frame, "SERVO SIMÜLASYONU", (x, y),
                    FONT, FONT_SCALE_S, COLOR_TEXT_CYAN, FONT_THICK_B)
        y += LINE_H - 4
        cv2.line(frame, (x, y), (panel_x + panel_w - PADDING, y), COLOR_BORDER, 1)
        y += 10

        # Her parmak için satır
        for name in finger_names:
            value = data.get(name, 0.0)
            angle = angles.get(name, 0)

            # İsim
            cv2.putText(frame, f"{name:<10s}", (x, y),
                        FONT, 0.44, COLOR_TEXT_WHITE, 1)

            # Progress bar
            bar_x = x + 90
            _draw_progress_bar(frame, bar_x, y - 10, value, width=110, height=10)

            # Değer metni
            cv2.putText(frame, f"{angle:3d}°", (bar_x + 118, y),
                        FONT, 0.44, COLOR_TEXT_GRAY, 1)

            y += 35

        # El bulunamazsa uyarı
        if not state.hand_detected:
            cv2.putText(frame, "(el yok - son konum)", (x, y),
                        FONT, 0.40, COLOR_TEXT_RED, 1)

    def _draw_no_hand_warning(self, frame, w, h):
        """Ekran ortasında 'El bulunamadı' mesajı."""
        text = "Eline kamerayi gosterin..."
        text_size = cv2.getTextSize(text, FONT, FONT_SCALE_L, FONT_THICK_B)[0]
        cx = (w - text_size[0]) // 2
        cy = h - 50
        cv2.putText(frame, text, (cx, cy),
                    FONT, FONT_SCALE_L, COLOR_TEXT_CYAN, FONT_THICK_B)
