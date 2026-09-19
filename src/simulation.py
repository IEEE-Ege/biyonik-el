"""
simulation.py -- SimulationController (guncellendi)

BionicHandState'ten beslenir.
Onceki HandState tabanli arayuz geriye donuk uyumluluk icin korundu.

Gelecekte bu dosyaya ArduinoController eklenecek.
"""

import abc
from bionic_hand_state import BionicHandState
import config as cfg


# -- Soyut arayuz -------------------------------------------------------------

class ControllerInterface(abc.ABC):
    """
    Biyonik el kontrol soyut arayuzu.

    Simdi: SimulationController, ArduinoController, MockArduinoController
    """

    @abc.abstractmethod
    def connect(self) -> bool:
        """Donanıma bağlanır. Simülasyon için her zaman True döner."""
        ...

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Donanım bağlantısını güvenle keser."""
        ...

    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Donanımın bağlı olup olmadığını döner."""
        ...

    @abc.abstractmethod
    def emergency_stop(self) -> None:
        """Sistemi acil durdurur ve servoları nötr/güvenli pozisyona çeker."""
        ...

    @abc.abstractmethod
    def get_mode_name(self) -> str:
        """'SIMULATION', 'ARDUINO', veya 'MOCK' döner."""
        ...

    @abc.abstractmethod
    def update(self, state: BionicHandState) -> None:
        """BionicHandState'i alip ilgili komutu gonderir / simule eder."""
        ...

    @abc.abstractmethod
    def get_display_data(self) -> dict[str, float]:
        """Gorsellestirme icin {parmak_adi: normalize_deger} sozlugu doner."""
        ...

    @abc.abstractmethod
    def get_servo_angles(self) -> dict[str, int]:
        """Guncel servo acilarini doner."""
        ...



# -- Simulasyon implementasyonu -----------------------------------------------

class SimulationController(ControllerInterface):
    """
    Servo hareketi simule eden controller.

    BionicHandState'i alir, hedef servo pozisyonlarini hesaplar,
    gorsellestirme ve terminal ciktisi icin sunar.

    Ilerde ArduinoController ile degistirilecek.
    """

    FINGER_NAMES = ["Basparmak", "Isaret", "Orta", "Yuzuk", "Serce"]
    SERVO_MIN_DEG = 0
    SERVO_MAX_DEG = 180

    def __init__(self):
        self._targets: dict[str, float] = {n: 0.0 for n in self.FINGER_NAMES}
        self._servo_angles: dict[str, int] = {n: cfg.SERVO_NEUTRAL_ANGLES[i] for i, n in enumerate(self.FINGER_NAMES)}
        self._last_state: BionicHandState | None = None
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def emergency_stop(self) -> None:
        for i, n in enumerate(self.FINGER_NAMES):
            self._targets[n] = 0.5
            self._servo_angles[n] = cfg.SERVO_NEUTRAL_ANGLES[i]

    def get_mode_name(self) -> str:
        return "SIMULATION"

    def update(self, state: BionicHandState) -> None:
        """BionicHandState'ten normalize degerleri al, servo acilarina cevir."""
        self._last_state = state
        values = state.targets()
        for name, value in zip(self.FINGER_NAMES, values):
            self._targets[name] = value
            angle = int(self.SERVO_MIN_DEG + value * (self.SERVO_MAX_DEG - self.SERVO_MIN_DEG))
            self._servo_angles[name] = angle

    def get_display_data(self) -> dict[str, float]:
        return dict(self._targets)

    def get_servo_angles(self) -> dict[str, int]:
        """Gercek servo acilari (ilerde Arduino'ya gonderilecek)."""
        return dict(self._servo_angles)

    def render_panel(self) -> list[str]:
        """Terminal icin ASCII panel."""
        BAR_WIDTH = 10
        lines = ["--- Simulasyon Paneli (Servo Hedefleri) ---"]
        for name in self.FINGER_NAMES:
            value = self._targets[name]
            angle = self._servo_angles[name]
            filled = int(value * BAR_WIDTH)
            bar = "#" * filled + "-" * (BAR_WIDTH - filled)
            pct = int(value * 100)
            lines.append(f"  {name:<12s} [{bar}]  {pct:3d}%  [{angle:3d} deg]")
        return lines
