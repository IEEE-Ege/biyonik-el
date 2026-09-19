"""
main.py -- Biyonik El Ana Uygulama Dongusu (Teslimat 3)

Pipeline:
  Camera
    -> HandDetector   (el tespiti, 21 landmark)
    -> HandState      (parmak durumu, normalize degerler)
    -> GestureDetector(temel el hareketleri analizi)
    -> MotionMapper   (kalibrasyon ile esleme)
    -> BionicHandSmoother (EMA + dead zone + hand lost)
    -> BionicHandState (biyonik el hedef degerleri)
    -> SimulationController (servo simulasyonu)
    -> Visualizer + BionicVisualizer + DiagnosticPanel
    -> DataLogger (CSV kayit)
"""

import sys
import os
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camera import Camera
from hand_detector import HandDetector
from gesture_detector import GestureDetector
from motion_mapper import MotionMapper
from smoother import BionicHandSmoother
from simulation import SimulationController
from arduino_controller import ArduinoController, MockArduinoController
from visualizer import Visualizer
from bionic_visualizer import BionicPanel, BionicHand2D, DiagnosticPanel
from data_logger import DataLogger
import config as cfg

def main():
    print("=" * 60)
    print("  BIYONIK EL -- El Hareketi Tanima (Teslimat 4)")
    print("=" * 60)
    print(f"  Smoothing alpha    : {cfg.SMOOTHING_ALPHA}")
    print(f"  Dead zone          : {cfg.DEAD_ZONE}")
    print("  Kontroller:")
    print("    [D] Diagnostic Mode Aç/Kapat")
    print("    [L] Logging Aç/Kapat")
    print("    [R] Smoother Sifirla")
    print("    [A] Arduino Moduna Geç")
    print("    [S] Simulation Moduna Geç")
    print("    [Q] / [ESC] Cikis\n")

    # -- Bilesenleri olustur --------------------------------------------------
    camera   = Camera(cfg.CAMERA_INDEX, cfg.CAMERA_WIDTH, cfg.CAMERA_HEIGHT)
    detector = HandDetector(
        max_num_hands=cfg.MP_MAX_HANDS,
        min_detection_confidence=cfg.MP_DETECTION_CONFIDENCE,
        min_tracking_confidence=cfg.MP_TRACKING_CONFIDENCE,
        min_presence_confidence=cfg.MP_PRESENCE_CONFIDENCE,
    )
    gesture_detector = GestureDetector()
    mapper   = MotionMapper()
    smoother = BionicHandSmoother()
    
    # Controllers
    sim_controller = SimulationController()
    sim_controller.connect() # Simülasyon her zaman bağlı
    
    arduino_controller = None # İhtiyaç duyulunca oluşturulacak
    
    current_controller = sim_controller
    
    logger   = DataLogger()

    # Gorsellestirme
    viz          = Visualizer(show_sim_panel=False)
    bionic_panel = BionicPanel()
    diag_panel   = DiagnosticPanel()
    hand_2d      = BionicHand2D(
        origin_x=cfg.CAMERA_WIDTH - 180,
        origin_y=cfg.CAMERA_HEIGHT - 200,
        scale=cfg.BIONIC_HAND_2D_SCALE,
    )

    diagnostic_mode = cfg.DEFAULT_DIAGNOSTIC_MODE

    # -- Kamerayi ac ----------------------------------------------------------
    if not camera.open():
        print("[HATA] Kamera acilamadi!")
        sys.exit(1)

    print(f"  Kamera acildi: {camera.width}x{camera.height}")
    print("  El gosterin...\n")

    window_name = "Biyonik El -- Motion Engine (Teslimat 4)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, cfg.CAMERA_WIDTH, cfg.CAMERA_HEIGHT)

    try:
        while True:
            ok, frame = camera.read()
            if not ok or frame is None:
                continue

            frame = cv2.flip(frame, 1)

            # ── PIPELINE ─────────────────────────────────────────────────────

            # 1. El tespiti
            hand_state = detector.process(frame)

            # 2. Gesture tespiti
            current_gesture = gesture_detector.update(hand_state)
            hand_2d.set_gesture(current_gesture)

            # 3. Motion mapping
            raw_bionic = mapper.map(hand_state)

            # 4. Smoothing + dead zone
            bionic = smoother.smooth(raw_bionic)

            # 5. Simulasyon / Arduino
            current_controller.update(bionic)

            # 6. Logging
            logger.log_frame(hand_state, bionic, current_gesture, camera.fps)

            # ── GORSELLESTIRME ────────────────────────────────────────────────

            frame = detector.draw_landmarks(frame, hand_state)

            if diagnostic_mode:
                # Diagnostic modda normal viz yerine diag panel
                frame = diag_panel.draw(frame, hand_state, bionic, current_gesture, camera.fps, logger.is_logging, current_controller)
            else:
                frame = viz.render(frame, hand_state, camera.fps, sim=None)

            if cfg.SHOW_2D_HAND:
                frame = hand_2d.draw(frame, bionic)

            if cfg.SHOW_BIONIC_PANEL:
                frame = bionic_panel.draw(frame, bionic)

            # ── KONTROLLER & CIKIS ────────────────────────────────────────────
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('d') or key == ord('D'):
                diagnostic_mode = not diagnostic_mode
                print(f"[BILGI] Diagnostic Mode: {'ACIK' if diagnostic_mode else 'KAPALI'}")
            elif key == ord('l') or key == ord('L'):
                state = logger.toggle_logging()
                print(f"[BILGI] Data Logging: {'ACIK' if state else 'KAPALI'}")
            elif key == ord('r') or key == ord('R'):
                smoother.reset()
                print("[BILGI] Smoother sifirlandi.")
            elif key == ord('s') or key == ord('S'):
                if current_controller != sim_controller:
                    current_controller.disconnect()
                    current_controller = sim_controller
                    print("[BILGI] Mod degistirildi: SIMULATION")
            elif key == ord('a') or key == ord('A'):
                if current_controller == sim_controller:
                    if arduino_controller is None:
                        # Gercek arduino portu kontrol edilebilir, simdilik fail-safe mock
                        arduino_controller = ArduinoController()
                        if not arduino_controller.connect():
                            print("[BILGI] Gercek donanim bulunamadi. MOCK ARDUINO baslatiliyor...")
                            arduino_controller = MockArduinoController()
                            arduino_controller.connect()
                    else:
                        arduino_controller.connect()
                    
                    current_controller = arduino_controller
                    print(f"[BILGI] Mod degistirildi: {current_controller.get_mode_name()}")

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    except KeyboardInterrupt:
        print("\n[BILGI] Ctrl+C ile durduruldu.")
    finally:
        logger.close()
        current_controller.disconnect()
        camera.release()
        detector.close()
        cv2.destroyAllWindows()
        print("[BILGI] Uygulama kapatildi.")

if __name__ == "__main__":
    main()
