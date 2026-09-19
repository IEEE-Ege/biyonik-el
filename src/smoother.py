"""
smoother.py -- Temporal smoothing + dead zone + hand lost isleme

BionicHandState degerlerini stabilize eder:

  1. EMA (Exponential Moving Average):
     Kamera landmark titresimlerini azaltir.
     smoothed = alpha * raw + (1-alpha) * previous

  2. Dead Zone:
     Minimum degisim esiginin altindaki guncellemeleri filtreler.
     Servo omrunu uzatir, gereksiz titremeleri onler.

  3. Hand Lost:
     El kameradan kayboldiginda config'deki HAND_LOST_BEHAVIOR'a gore davranir:
     - "HOLD_LAST"         : Son pozisyonu koru (guveli, ani hareket yok)
     - "RETURN_TO_NEUTRAL" : Yavashca notr pozisyona (NEUTRAL_POSITION) dogru kaydir
"""

import numpy as np
from bionic_hand_state import BionicHandState, BionicFingerTarget
import config as cfg


class BionicHandSmoother:
    """
    BionicHandState icin temporal smoothing, dead zone ve hand lost yoneticisi.

    Her kare icin:
      raw_bionic = MotionMapper.map(hand_state)
      smooth_bionic = smoother.smooth(raw_bionic)

    Parametreler (config.py'den alinir):
      alpha      -- EMA katsayisi [0.0, 1.0]
      dead_zone  -- Minimum degisim esigi
      behavior   -- Hand lost davranisi
    """

    def __init__(
        self,
        alpha: float = cfg.SMOOTHING_ALPHA,
        dead_zone: float = cfg.DEAD_ZONE,
        behavior: str = cfg.HAND_LOST_BEHAVIOR,
        neutral: float = cfg.NEUTRAL_POSITION,
        return_speed: float = cfg.RETURN_TO_NEUTRAL_SPEED,
    ):
        self.alpha = alpha
        self.dead_zone = dead_zone
        self.behavior = behavior
        self.neutral = neutral
        self.return_speed = return_speed

        # Onceki smoothed degerler (baslangicta notr pozisyon)
        self._prev = {
            "thumb":  neutral,
            "index":  neutral,
            "middle": neutral,
            "ring":   neutral,
            "pinky":  neutral,
        }

        # El tespiti durumu (hand_lost anlasmayi tespit icin)
        self._was_detected = False

    def smooth(self, raw: BionicHandState) -> BionicHandState:
        """
        Ham BionicHandState'e EMA + dead zone uygula, hand lost'u isle.

        Args:
            raw: MotionMapper'dan gelen ham BionicHandState

        Returns:
            Smoothed BionicHandState
        """
        # Hand lost tespiti
        hand_lost = self._was_detected and not raw.hand_detected
        self._was_detected = raw.hand_detected

        # Hedef degerleri topla
        raw_vals = {
            "thumb":  raw.thumb.raw,
            "index":  raw.index.raw,
            "middle": raw.middle.raw,
            "ring":   raw.ring.raw,
            "pinky":  raw.pinky.raw,
        }

        # Her parmak icin smooth uygula
        smooth_vals: dict[str, tuple[float, bool]] = {}

        for finger, raw_val in raw_vals.items():
            prev = self._prev[finger]

            if not raw.hand_detected:
                # El yok: davranisi uygula
                target, is_moving = self._handle_hand_lost(prev)
            else:
                # El var: EMA + dead zone
                target, is_moving = self._apply_ema_dead_zone(raw_val, prev)

            self._prev[finger] = target
            smooth_vals[finger] = (target, is_moving)

        # Smoothed BionicHandState olustur
        result = BionicHandState(
            hand_detected=raw.hand_detected,
            hand_lost=hand_lost,
            timestamp=raw.timestamp,
        )

        def _make_finger(fname: str, raw_target: float) -> BionicFingerTarget:
            s_val, moving = smooth_vals[fname]
            return BionicFingerTarget(
                target=round(s_val, 4),
                raw=round(raw_target, 4),
                is_moving=moving,
            )

        result.thumb  = _make_finger("thumb",  raw.thumb.raw)
        result.index  = _make_finger("index",  raw.index.raw)
        result.middle = _make_finger("middle", raw.middle.raw)
        result.ring   = _make_finger("ring",   raw.ring.raw)
        result.pinky  = _make_finger("pinky",  raw.pinky.raw)

        return result

    def _apply_ema_dead_zone(self, raw_val: float, prev: float) -> tuple[float, bool]:
        """
        EMA uygula, sonra dead zone kontrol et.

        Adimlar:
          1. EMA: smoothed = alpha * raw + (1-alpha) * prev
          2. Dead zone: |smoothed - prev| < dead_zone ise prev'i koru
        """
        # EMA
        ema = self.alpha * raw_val + (1.0 - self.alpha) * prev

        # Dead zone kontrol
        delta = abs(ema - prev)
        if delta < self.dead_zone:
            return prev, False  # Degisim cok kucuk, hareket yok

        return float(np.clip(ema, 0.0, 1.0)), True

    def _handle_hand_lost(self, prev: float) -> tuple[float, bool]:
        """
        El yokken davranisi uygula.

        HOLD_LAST: Son degeri koru, hareket yok.
        RETURN_TO_NEUTRAL: Yavas yavas notr pozisyona kaydir.
        """
        if self.behavior == "HOLD_LAST":
            return prev, False

        elif self.behavior == "RETURN_TO_NEUTRAL":
            # Nore dogru kucuk adimlarla kaydir
            diff = self.neutral - prev
            if abs(diff) < self.return_speed:
                return self.neutral, False
            direction = 1.0 if diff > 0 else -1.0
            new_val = prev + direction * self.return_speed
            is_moving = abs(diff) > self.dead_zone
            return float(np.clip(new_val, 0.0, 1.0)), is_moving

        return prev, False

    def reset(self, value: float | None = None) -> None:
        """
        Smoother'i sifirla. Arduino yeniden baglandiginda kullanisli.

        Args:
            value: Sifirlanacak deger. None ise NEUTRAL_POSITION kullanilir.
        """
        reset_val = value if value is not None else self.neutral
        for finger in self._prev:
            self._prev[finger] = reset_val

    @property
    def current_targets(self) -> dict[str, float]:
        """Mevcut smoothed degerlerin anlık snapshot'i."""
        return dict(self._prev)
