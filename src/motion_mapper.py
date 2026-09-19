"""
motion_mapper.py -- Motion Mapping katmani

HandState (insan eli) -> BionicHandState (biyonik el hedefi) donusumunu yapar.

Kalibrasyon altyapisi:
  Her parmak icin bagimsiz input/output min-max degerleri tanimlanabilir.
  Bu sayede:
    - Farkli kullanicilarin el anatomisi desteklenir
    - Servonun fiziksel hareket sinirini tanimlamak mumkun olur
    - Ileride kalibrasyon UI kolayca eklenebilir

Gelecek genisletmeler:
    - NonLinearMotionMapper: eg. karesol, sigmoidal eslemeler
    - GestureMapper: belirli hareketler icin ozel eslemeler
"""

import time
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from hand_state import HandState
from bionic_hand_state import BionicHandState, BionicFingerTarget
import config as cfg


@dataclass
class FingerCalibration:
    """
    Tek bir parmak icin kalibrasyon parametreleri.

    input_min/max  : Insan parmagi normalize degerinin beklenen araligi
                     Ornek: bir kullanicinin isaret parmagi hic 0.0'a inmiyorsa
                     input_min=0.15 yapilarak alt sinir kalibre edilir.

    output_min/max : Biyonik parmak ciktisinin araligi
                     Ornek: servonun mekanik limiti nedeniyle
                     output_max=0.90 yapilabilir.

    invert         : True ise esleme ters cevrilir.
                     Ornek: servonun montaj yonu ters ise.
    """
    input_min:  float = 0.0
    input_max:  float = 1.0
    output_min: float = 0.0
    output_max: float = 1.0
    invert:     bool  = False

    def apply(self, value: float) -> float:
        """
        Ham parmak degerini kalibre edilmis biyonik hedef degerine donusturur.

        Adimlar:
          1. input araligina gore klip ve normalize et
          2. output araligina esleme yap
          3. gerekirse ters cevir
        """
        if self.input_max == self.input_min:
            return self.output_min

        # Input araligina normalize et [0.0, 1.0]
        t = (value - self.input_min) / (self.input_max - self.input_min)
        t = float(np.clip(t, 0.0, 1.0))

        # Invert
        if self.invert:
            t = 1.0 - t

        # Output araligina esleme yap
        result = self.output_min + t * (self.output_max - self.output_min)
        return float(np.clip(result, 0.0, 1.0))


def _default_calibrations() -> dict[str, FingerCalibration]:
    """config.py'deki varsayilan degerlerden kalibrasyon nesneleri olustur."""
    cals = {}
    for finger, params in cfg.DEFAULT_FINGER_CALIBRATION.items():
        in_min, in_max, out_min, out_max, inv = params
        cals[finger] = FingerCalibration(
            input_min=in_min,
            input_max=in_max,
            output_min=out_min,
            output_max=out_max,
            invert=inv,
        )
    return cals


class MotionMapper:
    """
    HandState -> BionicHandState motion mapping katmani.

    Her parmak icin bagimsiz FingerCalibration uygulanir.
    Varsayilan olarak 1:1 dogrusal esleme kullanilir.

    Kullanim:
        mapper = MotionMapper()
        bionic = mapper.map(hand_state)

    Kalibrasyon guncelleme:
        mapper.set_calibration("thumb", FingerCalibration(input_min=0.1, ...))
    """

    def __init__(self):
        self._calibrations: dict[str, FingerCalibration] = _default_calibrations()

    def map(self, state: HandState) -> BionicHandState:
        """
        HandState'i BionicHandState'e donustur.

        Sadece mapping yapar -- smoothing veya dead zone UYGULAMAZ.
        Bu sorumluluk BionicHandSmoother'a aittir.
        """
        bionic = BionicHandState(
            hand_detected=state.hand_detected,
            hand_lost=False,
            timestamp=time.time(),
        )

        if not state.hand_detected:
            # El yokken raw degerleri sifirla, target'lara dokunma
            # (Smoother "hand lost" durumunu ele alacak)
            bionic.hand_lost = True
            return bionic

        # Her parmagi kalibrasyon ile esle
        bionic.thumb  = self._map_finger("thumb",  state.thumb.normalized)
        bionic.index  = self._map_finger("index",  state.index.normalized)
        bionic.middle = self._map_finger("middle", state.middle.normalized)
        bionic.ring   = self._map_finger("ring",   state.ring.normalized)
        bionic.pinky  = self._map_finger("pinky",  state.pinky.normalized)

        return bionic

    def _map_finger(self, finger_name: str, raw_normalized: float) -> BionicFingerTarget:
        """Tek bir parmak icin kalibrasyon uygula."""
        cal = self._calibrations.get(finger_name, FingerCalibration())
        mapped = cal.apply(raw_normalized)
        return BionicFingerTarget(
            target=mapped,  # Smoothing oncesi ham deger olarak da ayni degeri koy
            raw=mapped,     # Smoother raw'i okur, target'i gunceller
            is_moving=False,
        )

    def set_calibration(self, finger_name: str, calibration: FingerCalibration) -> None:
        """
        Belirli bir parmak icin kalibrasyon guncelle.

        Ileride kalibrasyon UI'sindan cagrilacak.

        Args:
            finger_name: "thumb", "index", "middle", "ring", "pinky"
            calibration: Yeni FingerCalibration nesnesi
        """
        if finger_name not in self._calibrations:
            raise ValueError(f"Bilinmeyen parmak: {finger_name}")
        self._calibrations[finger_name] = calibration

    def get_calibration(self, finger_name: str) -> FingerCalibration:
        """Belirli bir parmak icin mevcut kalibrasyonu don."""
        return self._calibrations.get(finger_name, FingerCalibration())

    def reset_calibrations(self) -> None:
        """Tum kalibrasyonlari varsayilana sifirla."""
        self._calibrations = _default_calibrations()
