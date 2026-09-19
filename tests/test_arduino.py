"""
test_arduino.py -- Arduino Entegrasyonu Birim Testleri

Serial protokol, güvenlik limitleri ve clamp fonksiyonlarını test eder.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../src'))

from bionic_hand_state import BionicHandState, BionicFingerTarget
from arduino_controller import MockArduinoController
import config as cfg

class TestArduinoIntegration(unittest.TestCase):

    def setUp(self):
        # Test izolasyonu icin konfigleri sabitle
        self.orig_max_step = cfg.SERVO_MAX_STEP_DEG
        self.orig_neutral = cfg.SERVO_NEUTRAL_ANGLES.copy()
        self.orig_max = cfg.SERVO_MAX_DEG
        
        cfg.SERVO_MAX_DEG = 90
        cfg.SERVO_MAX_STEP_DEG = 10
        cfg.SERVO_NEUTRAL_ANGLES = [0, 0, 0, 0, 0]
        
        self.controller = MockArduinoController()
        self.controller.connect()

    def tearDown(self):
        self.controller.disconnect()
        cfg.SERVO_MAX_STEP_DEG = self.orig_max_step
        cfg.SERVO_NEUTRAL_ANGLES = self.orig_neutral
        cfg.SERVO_MAX_DEG = self.orig_max

    def test_protocol_format(self):
        """Serial paketin istenen yapida olup olmadigini test et."""
        state = BionicHandState()
        # Tum hedef degerleri 0.5 yap
        state.thumb.target = 0.5
        state.index.target = 0.5
        state.middle.target = 0.5
        state.ring.target = 0.5
        state.pinky.target = 0.5
        
        cfg.SERVO_MAX_STEP_DEG = 0
        self.controller.update(state)
        packet = self.controller._build_serial_packet()
        
        # Beklenen format (max_deg=90 oldugundan 0.5 => 45): S,45,45,45,45,45\n
        self.assertEqual(packet, "S,45,45,45,45,45\n")

    def test_servo_clamping(self):
        """Acilarin 0-90 arasina sinirlandirildigini test et."""
        state = BionicHandState()
        state.thumb.target = -0.5
        state.index.target = 1.5
        state.middle.target = 0.0
        state.ring.target = 1.0
        state.pinky.target = 0.5
        
        # Max step'i kapat ki direkt hedefe ulassin (test icin)
        cfg.SERVO_MAX_STEP_DEG = 0
        
        self.controller.update(state)
        packet = self.controller._build_serial_packet()
        
        # Thumb -0.5 * 90 = -45 -> 0 olmali
        # Index 1.5 * 90 = 135 -> 90 olmali
        # Middle 0.0 -> 0
        # Ring 1.0 -> 90
        # Pinky 0.5 -> 45
        self.assertEqual(packet, "S,0,90,0,90,45\n")
        cfg.SERVO_MAX_STEP_DEG = 10 # Geri al

    def test_servo_max_step_safety(self):
        """Ani aci degisimlerinin adim adim yaklastirilmasi mekanizmasi."""
        state = BionicHandState()
        
        # Su an neutral (0) dayiz.
        # Hedefi 1.0 (90) yapalim. Eger MAX_STEP=10 ise, yeni aci 10 olmali.
        state.thumb.target = 1.0 # 90 derece
        self.controller.update(state)
        
        angles = self.controller.get_servo_angles()
        self.assertEqual(angles['Basparmak'], 10)
        
        # Ikinci kare
        self.controller.update(state)
        angles2 = self.controller.get_servo_angles()
        self.assertEqual(angles2['Basparmak'], 20)

    def test_emergency_stop(self):
        """Acil durdurmanin servolari notr pozisyona cektigini test et."""
        state = BionicHandState()
        state.thumb.target = 1.0
        
        cfg.SERVO_MAX_STEP_DEG = 0
        self.controller.update(state)
        
        angles = self.controller.get_servo_angles()
        self.assertEqual(angles['Basparmak'], 90)
        
        self.controller.emergency_stop()
        
        angles_after = self.controller.get_servo_angles()
        self.assertEqual(angles_after['Basparmak'], 0)

if __name__ == '__main__':
    unittest.main()
