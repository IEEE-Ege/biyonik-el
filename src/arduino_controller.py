"""
arduino_controller.py -- Arduino Hardware Controller

Fiziksel Arduino ve servolarla Serial port uzerinden iletisim kurar.
- MockArduinoController: Donanim bagli degilken log basarak test etmeyi saglar.
- ArduinoController: Gercek Serial uzerinden donanimi kontrol eder. (pyserial gerektirir)
"""

import time
import numpy as np
from simulation import ControllerInterface
from bionic_hand_state import BionicHandState
import config as cfg

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class ArduinoBaseController(ControllerInterface):
    """Ortak Arduino kontrol mantigi (Clamp, Step, vb)."""
    FINGER_NAMES = ["Basparmak", "Isaret", "Orta", "Yuzuk", "Serce"]

    def __init__(self):
        self._connected = False
        self._last_state: BionicHandState | None = None
        
        # Baslangicta hedefler ve mevcut acilar Notr pozisyonda
        self._targets: dict[str, float] = {n: 0.5 for n in self.FINGER_NAMES}
        self._servo_angles: dict[str, int] = {n: cfg.SERVO_NEUTRAL_ANGLES[i] for i, n in enumerate(self.FINGER_NAMES)}
        self._last_sent_time = 0

    def get_display_data(self) -> dict[str, float]:
        return dict(self._targets)

    def get_servo_angles(self) -> dict[str, int]:
        return dict(self._servo_angles)

    def is_connected(self) -> bool:
        return self._connected

    def emergency_stop(self) -> None:
        """Sistemi acil durdurur ve guvenli pozisyona ceker."""
        if not self._connected: return
        
        for i, n in enumerate(self.FINGER_NAMES):
            self._targets[n] = 0.5
            self._servo_angles[n] = cfg.SERVO_NEUTRAL_ANGLES[i]
        
        self._send_to_hardware()
        print("[ARDUINO] Emergency Stop - Nötr pozisyona gecildi.")

    def update(self, state: BionicHandState) -> None:
        """Hedefleri alir, step limitini uygular, guncel acilari hesaplar ve gonderir."""
        if not self._connected: return
        self._last_state = state
        
        targets = state.targets() # [thumb, index, middle, ring, pinky]
        angles = state.servo_angles(cfg.SERVO_MIN_DEG, cfg.SERVO_MAX_DEG)
        
        updated = False
        for i, n in enumerate(self.FINGER_NAMES):
            self._targets[n] = targets[i]
            target_angle = angles[n]
            current_angle = self._servo_angles[n]
            
            # Step limiti (Safety)
            if cfg.SERVO_MAX_STEP_DEG > 0:
                diff = target_angle - current_angle
                if abs(diff) > cfg.SERVO_MAX_STEP_DEG:
                    step = cfg.SERVO_MAX_STEP_DEG if diff > 0 else -cfg.SERVO_MAX_STEP_DEG
                    new_angle = current_angle + step
                else:
                    new_angle = target_angle
            else:
                new_angle = target_angle
                
            # Clamp
            new_angle = int(np.clip(new_angle, cfg.SERVO_MIN_DEG, cfg.SERVO_MAX_DEG))
            
            if self._servo_angles[n] != new_angle:
                self._servo_angles[n] = new_angle
                updated = True

        # Arduino timeout'a (2 sn) dusmesin diye surekli (heartbeat) paket gönderiyoruz
        current_time = time.time()
        
        # Eger acilar guncellendiyse HEMEN gonder
        if updated:
            self._send_to_hardware()
            self._last_sent_time = current_time
        # Degisme yoksa bile, saniyede en az 5 defa (0.2 sn) 'keep-alive' olarak gonder
        elif current_time - self._last_sent_time > 0.2:
            self._send_to_hardware()
            self._last_sent_time = current_time

    def _build_serial_packet(self) -> str:
        """Protokol: S,angle1,angle2,angle3,angle4,angle5\\n"""
        angles = [str(self._servo_angles[n]) for n in self.FINGER_NAMES]
        return f"S,{','.join(angles)}\n"

    def _send_to_hardware(self) -> None:
        raise NotImplementedError("Alt siniflar tarafindan implemente edilmeli")


class MockArduinoController(ArduinoBaseController):
    """Serial donanim bagli olmadiginda kullanilan Mock (Sahte) kontrolcu."""
    
    def connect(self) -> bool:
        print("[MOCK ARDUINO] Baglanti kuruldu. (Donanimsiz test modu)")
        self._connected = True
        self.emergency_stop() # Notr ile basla
        return True

    def disconnect(self) -> None:
        self.emergency_stop()
        self._connected = False
        print("[MOCK ARDUINO] Baglanti kesildi.")

    def get_mode_name(self) -> str:
        return "MOCK ARDUINO"

    def _send_to_hardware(self) -> None:
        packet = self._build_serial_packet()
        # Konsolu cok doldurmamasi icin belirli bir hizda (rate limit) print yapilabilir
        # ama su anlik debug amacli terminale basalim.
        # print(f"[MOCK SERIAL TX] {packet.strip()}")
        pass # Performans icin default olarak console spamini kapatiyorum.


class ArduinoController(ArduinoBaseController):
    """Gercek PySerial iletisimi kuran kontrolcu."""
    
    def __init__(self, port: str = cfg.ARDUINO_SERIAL_PORT, baudrate: int = cfg.ARDUINO_BAUDRATE):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None

    def connect(self) -> bool:
        if not SERIAL_AVAILABLE:
            print("[ARDUINO] HATA: pyserial yuklu degil! 'pip install pyserial' ile yukleyin.")
            return False

        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2) # Arduino'nun resetlenmesi ve ayaga kalkmasi icin bekle
            self._connected = True
            print(f"[ARDUINO] Baglanti kuruldu: {self.port} @ {self.baudrate}")
            self.emergency_stop() # Guvenli baslangic
            return True
        except Exception as e:
            print(f"[ARDUINO] Baglanti HATA: {self.port} - {str(e)}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        if self._connected and self.serial_conn:
            try:
                self.emergency_stop()
                time.sleep(0.1)
                self.serial_conn.close()
                print(f"[ARDUINO] Baglanti kapatildi: {self.port}")
            except Exception as e:
                print(f"[ARDUINO] Kapatma HATA: {str(e)}")
        self._connected = False

    def get_mode_name(self) -> str:
        return "ARDUINO"

    def _send_to_hardware(self) -> None:
        if not self._connected or not self.serial_conn:
            return
        
        packet = self._build_serial_packet()
        try:
            self.serial_conn.write(packet.encode('ascii'))
            self.serial_conn.flush()
            # Debug: terminale gönderilen paketi göster
            print(f"[TX] {packet.strip()}", end='\r')
        except Exception as e:
            print(f"[ARDUINO] Yazma HATA: {str(e)}")
            self.disconnect()
