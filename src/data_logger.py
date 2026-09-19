"""
data_logger.py -- Diagnostic Data Logging Modülü

Sistem davranışını CSV formatında loglamak için kullanılır.
Diagnostic, raw, smooth, ve target verilerini depolar.
"""

import os
import csv
import time
from datetime import datetime
from hand_state import HandState
from bionic_hand_state import BionicHandState
import config as cfg

class DataLogger:
    def __init__(self, log_dir: str = cfg.LOG_DIR):
        self.log_dir = log_dir
        self.is_logging = False
        self.csv_file = None
        self.csv_writer = None

    def start_logging(self):
        """Yeni bir CSV dosyası oluşturur ve logging'i başlatır."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.log_dir, f"bionic_log_{timestamp_str}.csv")
        
        self.csv_file = open(filepath, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        
        # Header yaz
        header = [
            "timestamp", "fps", "handedness", "gesture",
            "thumb_raw", "index_raw", "middle_raw", "ring_raw", "pinky_raw",
            "thumb_smooth", "index_smooth", "middle_smooth", "ring_smooth", "pinky_smooth",
            "thumb_target", "index_target", "middle_target", "ring_target", "pinky_target"
        ]
        self.csv_writer.writerow(header)
        self.is_logging = True
        print(f"[LOGGING] Baslatildi: {filepath}")

    def stop_logging(self):
        """Logging'i durdurur ve dosyayı kapatır."""
        if self.is_logging and self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            self.is_logging = False
            print("[LOGGING] Durduruldu.")

    def toggle_logging(self) -> bool:
        """Logging durumunu tersine çevirir (Aç/Kapat)."""
        if self.is_logging:
            self.stop_logging()
        else:
            self.start_logging()
        return self.is_logging

    def log_frame(self, state: HandState, bionic: BionicHandState, gesture: str, fps: float):
        """Eğer logging açıksa verileri CSV dosyasına yazar."""
        if not self.is_logging or not self.csv_writer:
            return

        row = [
            time.time(),
            round(fps, 1),
            state.handedness if state.hand_detected else "None",
            gesture,
            # RAW Normalized
            round(state.thumb.normalized, 3) if state.hand_detected else 0.0,
            round(state.index.normalized, 3) if state.hand_detected else 0.0,
            round(state.middle.normalized, 3) if state.hand_detected else 0.0,
            round(state.ring.normalized, 3) if state.hand_detected else 0.0,
            round(state.pinky.normalized, 3) if state.hand_detected else 0.0,
            # SMOOTH 
            round(bionic.thumb.raw, 3) if not bionic.hand_lost else 0.0, # smoothed before mapping ? Wait, bionic.thumb.raw is mapped output before smooth. Actually bionic.thumb.target is smoothed output. Let's log target.
            round(bionic.index.raw, 3) if not bionic.hand_lost else 0.0,
            round(bionic.middle.raw, 3) if not bionic.hand_lost else 0.0,
            round(bionic.ring.raw, 3) if not bionic.hand_lost else 0.0,
            round(bionic.pinky.raw, 3) if not bionic.hand_lost else 0.0,
            # TARGET (Smooth uygulanmış hedef)
            round(bionic.thumb.target, 3),
            round(bionic.index.target, 3),
            round(bionic.middle.target, 3),
            round(bionic.ring.target, 3),
            round(bionic.pinky.target, 3)
        ]
        self.csv_writer.writerow(row)

    def close(self):
        self.stop_logging()
