"""
bionic_hand_state.py -- BionicHandState veri yapısı

Bu modül biyonik elin hedef durumunu temsil eder.
HandState (insan eli) → BionicHandState (biyonik el hedefi) dönüşümü
MotionMapper tarafından yapılır.

BionicHandState, ileride Arduino Controller'a doğrudan beslenecek.
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BionicFingerTarget:
    """
    Tek bir biyonik parmağın hedef durumu.

    Alanlar:
        target     — Hedef pozisyon [0.0=açık, 1.0=kapalı]
        raw        — Smoothing öncesi ham değer
        is_moving  — Dead zone'dan çıkıp hareket ediyor mu?
    """
    target: float = 0.0
    raw: float = 0.0
    is_moving: bool = False

    def servo_angle(self, min_deg: float = 0.0, max_deg: float = 180.0) -> int:
        """
        Servo açısına dönüştür.
        Arduino'ya gönderilecek PWM değeri için kullanılır.
        """
        return int(min_deg + self.target * (max_deg - min_deg))


@dataclass
class BionicHandState:
    """
    Biyonik elin bütüncül hedef durumu.

    Bu yapı sistemin merkez veri modelidir:
      - MotionMapper bu yapıyı doldurur.
      - Smoother bu yapı üzerinde düzeltme uygular.
      - SimulationController bu yapıyı okur.
      - (İleride) ArduinoController bu yapıyı okuyarak servo açılarını gönderir.

    Alanlar:
        hand_detected  — Kamerada el tespit edildi mi?
        hand_lost      — El az önce kayboldu mu? (hand_detected False → True geçişi)
        timestamp      — Bu state'in oluşturulma zamanı (Unix timestamp)
        thumb/index/middle/ring/pinky — Parmak hedef değerleri
    """
    hand_detected: bool = False
    hand_lost: bool = False
    timestamp: float = field(default_factory=time.time)

    thumb:  BionicFingerTarget = field(default_factory=BionicFingerTarget)
    index:  BionicFingerTarget = field(default_factory=BionicFingerTarget)
    middle: BionicFingerTarget = field(default_factory=BionicFingerTarget)
    ring:   BionicFingerTarget = field(default_factory=BionicFingerTarget)
    pinky:  BionicFingerTarget = field(default_factory=BionicFingerTarget)

    def targets(self) -> list[float]:
        """5 parmak hedef değerini liste olarak döner [thumb..pinky]."""
        return [
            self.thumb.target,
            self.index.target,
            self.middle.target,
            self.ring.target,
            self.pinky.target,
        ]

    def raw_values(self) -> list[float]:
        """Smoothing öncesi ham değerler."""
        return [
            self.thumb.raw,
            self.index.raw,
            self.middle.raw,
            self.ring.raw,
            self.pinky.raw,
        ]

    def as_dict(self) -> dict[str, float]:
        """İsimli sözlük olarak hedef değerler."""
        return {
            "Basparmak": self.thumb.target,
            "Isaret":    self.index.target,
            "Orta":      self.middle.target,
            "Yuzuk":     self.ring.target,
            "Serce":     self.pinky.target,
        }

    def servo_angles(self, min_deg: float = 0.0, max_deg: float = 180.0) -> dict[str, int]:
        """
        Tüm parmaklar için servo açılarını döner.
        İleride ArduinoController'a gönderilecek değerler.
        """
        return {
            "Basparmak": self.thumb.servo_angle(min_deg, max_deg),
            "Isaret":    self.index.servo_angle(min_deg, max_deg),
            "Orta":      self.middle.servo_angle(min_deg, max_deg),
            "Yuzuk":     self.ring.servo_angle(min_deg, max_deg),
            "Serce":     self.pinky.servo_angle(min_deg, max_deg),
        }

    def any_moving(self) -> bool:
        """Herhangi bir parmak hareket ediyor mu?"""
        return any([
            self.thumb.is_moving,
            self.index.is_moving,
            self.middle.is_moving,
            self.ring.is_moving,
            self.pinky.is_moving,
        ])

    def __str__(self) -> str:
        status = "TESPIT EDILDI" if self.hand_detected else "KAYIP" if self.hand_lost else "YOK"
        lines = [f"BionicHandState [{status}]"]
        for name, val in self.as_dict().items():
            bar_w = 10
            filled = int(val * bar_w)
            bar = "#" * filled + "-" * (bar_w - filled)
            lines.append(f"  {name:<12s} [{bar}] {val*100:5.1f}%")
        return "\n".join(lines)
