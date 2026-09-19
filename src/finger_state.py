"""
finger_state.py -- Parmak geometri hesaplama modulu

MediaPipe landmark'larindan her parmak icin:
  - Geometrik kivirilma acisi (vektor carpimi ile)
  - OPEN/CLOSED durumu
  - [0.0, 1.0] normalize deger

hesaplar.

MediaPipe El Landmark Indeksleri:
  0: WRIST
  1: THUMB_CMC   2: THUMB_MCP   3: THUMB_IP    4: THUMB_TIP
  5: INDEX_MCP   6: INDEX_PIP   7: INDEX_DIP   8: INDEX_TIP
  9: MIDDLE_MCP 10: MIDDLE_PIP 11: MIDDLE_DIP 12: MIDDLE_TIP
 13: RING_MCP   14: RING_PIP   15: RING_DIP   16: RING_TIP
 17: PINKY_MCP  18: PINKY_PIP  19: PINKY_DIP  20: PINKY_TIP
"""

import math
import numpy as np
from hand_state import FingerState

# -- Landmark indeks sabitleri -------------------------------------------------
WRIST = 0

THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

# -- Esik degerler -------------------------------------------------------------
FINGER_OPEN_THRESHOLD_DEG = 160.0


def _landmark_to_array(lm) -> np.ndarray:
    """MediaPipe landmark objesini numpy dizisine cevirir."""
    return np.array([lm.x, lm.y, lm.z], dtype=float)


def _angle_between_three_points(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """
    b noktasinda olusan acıyı hesaplar (a-b-c ucgeni).
    arccos(dot(BA, BC) / (|BA| * |BC|))
    Returns: Aci (derece), [0, 180] araliginda
    """
    ba = a - b
    bc = c - b
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-9 or norm_bc < 1e-9:
        return 0.0
    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    return math.degrees(math.acos(float(np.clip(cos_angle, -1.0, 1.0))))


def _normalize_angle(angle_deg: float, min_angle: float, max_angle: float) -> float:
    """Aciyi [0.0, 1.0] araligina normalize eder."""
    if max_angle == min_angle:
        return 0.0
    return float(np.clip((angle_deg - min_angle) / (max_angle - min_angle), 0.0, 1.0))


# -- Parmak hesaplama fonksiyonlari --------------------------------------------

def compute_thumb(lms: list, handedness: str) -> FingerState:
    """
    Basparmak acik/kapali tespiti — kamera acisina ve el yonune bagimsiz.

    TEMEL ILKE:
      "Kapali basparmak" = basparmak ucu avuc icine yakin (kivrilmis/cekimis)
      "Acik basparmak"   = basparmak ucu avuc icindan uzak (uzatilmis, her yonde)

    YONTEM — IKI metrigin agirlikli birlestimi:

    1. TIP-PALM MESAFESI [agirlik %65]
       THUMB_TIP'in avuc merkezi (4 parmak MCP ortalamasi) arasindaki mesafe,
       el buyuklugune (WRIST-MIDDLE_MCP mesafesi) gore normalize edilir.
       Sonuc kamera uzakligina ve el yonune BAGIMSIZ.

       Kapali: ~%15-25 el buyuklugu
       Acik:   ~%60-100 el buyuklugu

    2. EKLEM CURL ACISI [agirlik %35]
       (CMC->MCP->IP + MCP->IP->TIP) ortalamasi.
       Basparmak kivrildiginda bu acilar kucuelur.
       Tip-mesafe tek basina yeterli olmayan kapali pozisyonlari destekler.
    """
    wrist      = _landmark_to_array(lms[WRIST])
    thumb_cmc  = _landmark_to_array(lms[THUMB_CMC])
    thumb_mcp  = _landmark_to_array(lms[THUMB_MCP])
    thumb_ip   = _landmark_to_array(lms[THUMB_IP])
    thumb_tip  = _landmark_to_array(lms[THUMB_TIP])
    index_mcp  = _landmark_to_array(lms[INDEX_MCP])
    middle_mcp = _landmark_to_array(lms[MIDDLE_MCP])
    ring_mcp   = _landmark_to_array(lms[RING_MCP])
    pinky_mcp  = _landmark_to_array(lms[PINKY_MCP])

    # -- 1. Tip -> Palm merkezi mesafesi (el olcegine gore normalize) ----------
    # Avuc merkezi: 4 parmak MCP'sinin ortalamasi
    palm_center = (index_mcp + middle_mcp + ring_mcp + pinky_mcp) / 4.0

    # El olcegi: bilek -> orta parmak MCP mesafesi (kamera uzakligini iptal eder)
    hand_scale = np.linalg.norm(middle_mcp - wrist)

    tip_to_palm_dist = np.linalg.norm(thumb_tip - palm_center)

    if hand_scale > 1e-9:
        # Olcekli mesafe: 0.0 = tip avuc merkezinde, 1.0+ = tamamen uzatilmis
        scaled_dist = tip_to_palm_dist / hand_scale
    else:
        scaled_dist = 0.0

    # Normalize: 0.25 el olcegi = kapali (0.0), 0.80 el olcegi = tam acik (1.0)
    # Gercek olcumler: kapali ~0.15-0.35, acik ~0.65-1.0
    norm_dist = float(np.clip((scaled_dist - 0.25) / (0.80 - 0.25), 0.0, 1.0))

    # -- 2. Eklem curl acisi --------------------------------------------------
    mcp_curl = _angle_between_three_points(thumb_cmc, thumb_mcp, thumb_ip)
    ip_curl  = _angle_between_three_points(thumb_mcp, thumb_ip, thumb_tip)
    avg_curl = (mcp_curl * 0.5 + ip_curl * 0.5)

    # Normalize: 110 derece = kivrik/kapali, 175 derece = duz/acik
    norm_curl = _normalize_angle(avg_curl, min_angle=110.0, max_angle=175.0)

    # -- Agirlikli birlesim ---------------------------------------------------
    # Eski: 1.0 = acik, 0.0 = kapali
    # Yeni SEMANTIK: 0.0 = acik, 1.0 = kapali
    openness = float(np.clip(0.65 * norm_dist + 0.35 * norm_curl, 0.0, 1.0))
    normalized = round(1.0 - openness, 3)

    # OPEN/CLOSED esigi (Eski openness >= 0.40 idi, simdi normalized <= 0.60)
    is_open = normalized <= 0.60

    # angle_deg: eklem curl acisini goster (kullaniciya anlamli bilgi)
    return FingerState(
        is_open=is_open,
        angle_deg=round(avg_curl, 1),
        normalized=normalized,
    )


def _compute_long_finger(
    lms: list,
    mcp_idx: int,
    pip_idx: int,
    dip_idx: int,
    tip_idx: int,
) -> FingerState:
    """
    Isaret, orta, yuzuk ve serce parmak icin genel hesaplama.
    MCP, PIP, DIP eklem acilari agirlikli ortalamasiyla aciklik belirlenir.
    """
    mcp_angle = _angle_between_three_points(
        _landmark_to_array(lms[WRIST]),
        _landmark_to_array(lms[mcp_idx]),
        _landmark_to_array(lms[pip_idx]),
    )
    pip_angle = _angle_between_three_points(
        _landmark_to_array(lms[mcp_idx]),
        _landmark_to_array(lms[pip_idx]),
        _landmark_to_array(lms[dip_idx]),
    )
    dip_angle = _angle_between_three_points(
        _landmark_to_array(lms[pip_idx]),
        _landmark_to_array(lms[dip_idx]),
        _landmark_to_array(lms[tip_idx]),
    )

    avg_angle = (mcp_angle * 0.5 + pip_angle * 0.3 + dip_angle * 0.2)

    is_open = avg_angle >= FINGER_OPEN_THRESHOLD_DEG
    
    # Eski: 1.0 = acik, 0.0 = kapali
    # Yeni SEMANTIK: 0.0 = acik, 1.0 = kapali
    openness = _normalize_angle(avg_angle, min_angle=85.0, max_angle=175.0)
    normalized = round(1.0 - openness, 3)

    return FingerState(
        is_open=is_open,
        angle_deg=round(avg_angle, 1),
        normalized=normalized,
    )


def compute_index(lms: list) -> FingerState:
    return _compute_long_finger(lms, INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP)


def compute_middle(lms: list) -> FingerState:
    return _compute_long_finger(lms, MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP)


def compute_ring(lms: list) -> FingerState:
    return _compute_long_finger(lms, RING_MCP, RING_PIP, RING_DIP, RING_TIP)


def compute_pinky(lms: list) -> FingerState:
    return _compute_long_finger(lms, PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP)


def compute_all_fingers(lms: list, handedness: str) -> dict[str, FingerState]:
    """Tum parmaklari hesapla, isimli sozluk olarak doondur."""
    return {
        "thumb":  compute_thumb(lms, handedness),
        "index":  compute_index(lms),
        "middle": compute_middle(lms),
        "ring":   compute_ring(lms),
        "pinky":  compute_pinky(lms),
    }
