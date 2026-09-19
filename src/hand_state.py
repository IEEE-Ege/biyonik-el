"""
hand_state.py — El ve parmak durum veri yapıları

HandState, uygulamanın temel veri modeli görevi görür.
İleride Arduino katmanı doğrudan bu yapıdan beslenecek.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FingerState:
    """
    Tek bir parmağın durum bilgisi.

    Alanlar:
        is_open       — True: açık, False: kapalı
        angle_deg     — Parmağın geometrik kıvrılma açısı (derece, 0=tam kapalı, ~180=tam açık)
        normalized    — Servo kontrolü için normalize değer [0.0=kapalı, 1.0=açık]
    """

    is_open: bool = False
    angle_deg: float = 0.0
    normalized: float = 0.0

    def __str__(self) -> str:
        durum = "ACIK  " if self.is_open else "KAPALI"
        return f"{durum} | aci={self.angle_deg:5.1f}  | norm={self.normalized:.2f}"


@dataclass
class HandState:
    """
    Bir elin bütüncül durum temsili.

    Bu veri yapısı şu an görselleştirme ve simülasyon için kullanılır.
    İleride ArduinoController doğrudan bu yapıyı okuyacak.

    Alanlar:
        hand_detected  — El görüntüde tespit edildi mi?
        handedness     — "Sol" | "Sağ" | None
        thumb          — Başparmak durumu
        index          — İşaret parmağı durumu
        middle         — Orta parmak durumu
        ring           — Yüzük parmağı durumu
        pinky          — Serçe parmak durumu
        landmarks      — MediaPipe'dan gelen ham landmark listesi (normalize koordinatlar)
        wrist_pos      — Bilek pozisyonu (piksel koordinatları), görselleştirme için
    """

    hand_detected: bool = False
    handedness: Optional[str] = None

    thumb: FingerState = field(default_factory=FingerState)
    index: FingerState = field(default_factory=FingerState)
    middle: FingerState = field(default_factory=FingerState)
    ring: FingerState = field(default_factory=FingerState)
    pinky: FingerState = field(default_factory=FingerState)

    # Ham landmark verileri (MediaPipe NormalizedLandmarkList)
    landmarks: list = field(default_factory=list)

    # Bilek piksel konumu (görselleştirme için)
    wrist_pos: tuple[int, int] = (0, 0)

    def fingers(self) -> dict[str, FingerState]:
        """Tüm parmakları isimli sözlük olarak döner."""
        return {
            "Basparmak": self.thumb,
            "Isaret": self.index,
            "Orta": self.middle,
            "Yuzuk": self.ring,
            "Serce": self.pinky,
        }

    def normalized_values(self) -> list[float]:
        """Servo kontrolü için 5 normalize değer [thumb, index, middle, ring, pinky]."""
        return [
            self.thumb.normalized,
            self.index.normalized,
            self.middle.normalized,
            self.ring.normalized,
            self.pinky.normalized,
        ]

    def open_count(self) -> int:
        """Açık parmak sayısı."""
        return sum(1 for f in self.fingers().values() if f.is_open)

    def reset(self):
        """El bulunamazsa durumu sıfırla."""
        self.hand_detected = False
        self.handedness = None
        self.thumb = FingerState()
        self.index = FingerState()
        self.middle = FingerState()
        self.ring = FingerState()
        self.pinky = FingerState()
        self.landmarks = []
        self.wrist_pos = (0, 0)

    def __str__(self) -> str:
        if not self.hand_detected:
            return "El tespit edilmedi."
        lines = [
            f"El: {self.handedness} | Acik parmak: {self.open_count()}/5",
        ]
        for name, finger in self.fingers().items():
            lines.append(f"  {name:12s}: {finger}")
        return "\n".join(lines)
