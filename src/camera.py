"""
camera.py — Kamera yönetimi modülü

Webcam'den frame okuma, FPS hesaplama ve kaynak yönetimini sağlar.
"""

import time
import cv2


class Camera:
    """
    OpenCV webcam sarmalayıcısı.
    Context manager olarak kullanılabilir:
        with Camera() as cam:
            frame = cam.read()
    """

    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None

        # FPS hesaplama
        self._prev_time: float = 0.0
        self._fps: float = 0.0

    def open(self) -> bool:
        """Kamerayı aç. Başarılıysa True döner."""
        self._cap = cv2.VideoCapture(self.camera_index)
        if not self._cap.isOpened():
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, 30)
        return True

    def read(self) -> tuple[bool, cv2.typing.MatLike | None]:
        """
        Bir frame oku.
        Returns:
            (başarılı, frame) — başarısızsa frame None olur
        """
        if self._cap is None or not self._cap.isOpened():
            return False, None

        success, frame = self._cap.read()
        if success:
            # FPS güncelle
            current_time = time.time()
            if self._prev_time > 0:
                elapsed = current_time - self._prev_time
                self._fps = 1.0 / elapsed if elapsed > 0 else 0.0
            self._prev_time = current_time

        return success, frame

    @property
    def fps(self) -> float:
        """Son hesaplanan FPS değeri."""
        return self._fps

    def release(self):
        """Kamera kaynağını serbest bırak."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def __enter__(self):
        if not self.open():
            raise RuntimeError(
                f"Kamera {self.camera_index} açılamadı. "
                "Kameranın bağlı ve başka bir uygulama tarafından kullanılmıyor olduğundan emin olun."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False
