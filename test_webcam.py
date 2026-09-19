"""
test_webcam.py -- Webcam + Teslimat 2 Pipeline Testi

8 saniye calisir ve sonuclari raporlar.
Smoothing, dead zone, hand lost davranisini gozlemlemek icin kullanilabilir.
"""

import sys, os, time
import cv2, numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from camera import Camera
from hand_detector import HandDetector
from motion_mapper import MotionMapper
from smoother import BionicHandSmoother
from simulation import SimulationController
from visualizer import Visualizer
from bionic_visualizer import BionicPanel, BionicHand2D
import config as cfg


def test_pipeline(duration=8):
    print("=" * 55)
    print("  BIYONIK EL -- Pipeline Entegrasyon Testi")
    print("=" * 55)
    print(f"  Sure: {duration} saniye | 'q' ile erken cikis\n")

    camera   = Camera(cfg.CAMERA_INDEX, cfg.CAMERA_WIDTH, cfg.CAMERA_HEIGHT)
    if not camera.open():
        print("[HATA] Kamera acilamadi!"); return

    detector     = HandDetector()
    mapper       = MotionMapper()
    smoother     = BionicHandSmoother()
    sim          = SimulationController()
    viz          = Visualizer(show_sim_panel=False)
    bionic_panel = BionicPanel()
    hand_2d      = BionicHand2D(
        origin_x=cfg.CAMERA_WIDTH - 180,
        origin_y=cfg.CAMERA_HEIGHT - 200,
        scale=cfg.BIONIC_HAND_2D_SCALE,
    )

    window = "TEST -- Biyonik El Pipeline"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, cfg.CAMERA_WIDTH, cfg.CAMERA_HEIGHT)

    frames = hand_frames = 0
    max_fps = 0.0
    hand_lost_events = 0
    prev_detected = False
    start = time.time()

    try:
        while time.time() - start < duration:
            ok, frame = camera.read()
            if not ok: continue
            frame = cv2.flip(frame, 1)

            hand_state = detector.process(frame)
            raw_bionic = mapper.map(hand_state)
            bionic     = smoother.smooth(raw_bionic)
            sim.update(bionic)

            if bionic.hand_lost:
                hand_lost_events += 1

            frame = detector.draw_landmarks(frame, hand_state)
            frame = viz.render(frame, hand_state, camera.fps, sim=None)
            frame = hand_2d.draw(frame, bionic)
            frame = bionic_panel.draw(frame, bionic)

            rem = duration - (time.time() - start)
            cv2.putText(frame, f"Test: {rem:.1f}s kaldi",
                        (cfg.CAMERA_WIDTH//2 - 100, cfg.CAMERA_HEIGHT - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
            cv2.imshow(window, frame)

            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break

            frames += 1
            if hand_state.hand_detected: hand_frames += 1
            if camera.fps > max_fps: max_fps = camera.fps
            prev_detected = hand_state.hand_detected

    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()

    pct = hand_frames / frames * 100 if frames > 0 else 0
    print("\n--- TEST SONUCLARI ---")
    print(f"  Okunan frame       : {frames}")
    print(f"  El tespit edilen   : {hand_frames} ({pct:.1f}%)")
    print(f"  Hand lost olayi    : {hand_lost_events}")
    print(f"  Maksimum FPS       : {max_fps:.1f}")
    print(f"  Smoothing alpha    : {cfg.SMOOTHING_ALPHA}")
    print(f"  Dead zone          : {cfg.DEAD_ZONE}")
    print(f"  Hand lost davranis : {cfg.HAND_LOST_BEHAVIOR}")
    print()
    if frames > 0: print("  [OK] Pipeline calisiyor")
    if hand_frames > 0: print("  [OK] El tespiti calisiyor")


if __name__ == "__main__":
    test_pipeline(duration=8)
