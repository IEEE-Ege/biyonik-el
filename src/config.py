"""
config.py -- Merkezi konfigürasyon modülü

Tüm ayarlanabilir parametreler burada tanımlanır.
Değiştirilmek istenen her parametre için tek bir yer.

Gelecekte bu dosya bir JSON/YAML config'e dönüştürülebilir.
"""

# ==============================================================================
# MOTION MAPPING
# ==============================================================================

# Her parmak için varsayılan kalibrasyon değerleri.
# Kullanıcıya göre input_min/input_max ayarlanabilir.
# Örnek: bazı kişilerin başparmağı asla 0.0'a inmiyor olabilir.
DEFAULT_FINGER_CALIBRATION = {
    # finger_name: (input_min, input_max, output_min, output_max, invert)
    "thumb":  (0.0, 1.0, 0.0, 1.0, False),
    "index":  (0.0, 1.0, 0.0, 1.0, False),
    "middle": (0.0, 1.0, 0.0, 1.0, False),
    "ring":   (0.0, 1.0, 0.0, 1.0, False),
    "pinky":  (0.0, 1.0, 0.0, 1.0, False),
}

# ==============================================================================
# SMOOTHING
# ==============================================================================

# Exponential Moving Average katsayısı.
# Formül: smoothed = ALPHA * raw + (1 - ALPHA) * previous
#
# Değer seçim mantığı:
#   0.1  → Çok yumuşak, ~10 frame gecikme. Servo titremez ama hareket yavaş.
#   0.25 → Dengeli seçim. ~4 frame gecikme. Titreşim düşük, hareket akıcı.
#   0.5  → Hızlı tepki, az düzeltme. Hafif titreşim kalabilir.
#   1.0  → Ham değer, smoothing yok.
#
# 30fps'de ALPHA=0.25 → ~133ms gecikme → servo kontrolü için kabul edilebilir.
SMOOTHING_ALPHA = 0.6   # Test: hızlı tepki (eskisi 0.25 idi)

# ==============================================================================
# DEAD ZONE
# ==============================================================================

# Minimum değişim eşiği.
# Mevcut değer ile yeni değer arasındaki fark bu eşikten küçükse,
# yeni değer işlenmez — son değer korunur.
#
# Normalize değer [0.0, 1.0] üzerinde:
#   0.01 = %1 değişim filtresi (çok hassas)
#   0.02 = %2 değişim filtresi (dengeli seçim)
#   0.05 = %5 değişim filtresi (daha agresif filtreleme)
#
# Servo ömrünü uzatır ve gereksiz titremeleri önler.
DEAD_ZONE = 0.02

# ==============================================================================
# HAND LOST DAVRANIŞI
# ==============================================================================

# El kameradan kaybolduğunda ne yapılacak:
#
#   "HOLD_LAST"        → Son bilinen pozisyonu koru.
#                        Servo için güvenli: ani hareket yok.
#                        Varsayılan ve önerilen.
#
#   "RETURN_TO_NEUTRAL" → Kontrollü şekilde nötr pozisyona (0.5) doğru kaydır.
#                         Her frame'de RETURN_SPEED kadar nötre yaklaşır.
#
HAND_LOST_BEHAVIOR = "HOLD_LAST"

# RETURN_TO_NEUTRAL seçilirse, her frame'de bu kadar hareket eder.
# Küçük değer = yavaş/yumuşak geçiş, büyük değer = hızlı geçiş.
RETURN_TO_NEUTRAL_SPEED = 0.03

# Nötr pozisyon (tamamen açık = 0.0, tamamen kapalı = 1.0, yarı = 0.5)
NEUTRAL_POSITION = 0.0

# ==============================================================================
# KAMERA
# ==============================================================================
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# ==============================================================================
# MEDIAPIPE HAND DETECTOR
# ==============================================================================
MP_MAX_HANDS = 1
MP_DETECTION_CONFIDENCE = 0.7
MP_TRACKING_CONFIDENCE = 0.6
MP_PRESENCE_CONFIDENCE = 0.5

# ==============================================================================
# GÖRSELLEŞTIRME
# ==============================================================================
SHOW_SIM_PANEL = True       # Sağ üstte servo simülasyon paneli
SHOW_BIONIC_PANEL = True    # Alt kısımda biyonik el progress bar paneli
SHOW_2D_HAND = True         # 2D biyonik el çizimi

# 2D el çizim konumu (pencere içinde, sol-alt köşe referans)
BIONIC_HAND_2D_X = 20
BIONIC_HAND_2D_Y = 420
BIONIC_HAND_2D_SCALE = 90   # piksel cinsinden el ölçeği
# ==============================================================================
# GESTURE RECOGNITION
# ==============================================================================

# Gesture'ın değişmesi için peş peşe kaç frame aynı kalması gerektiği (Debounce)
GESTURE_STABILITY_FRAMES = 5

# ==============================================================================
# LOGGING & DIAGNOSTICS
# ==============================================================================
LOG_DIR = "logs"
DEFAULT_LOGGING_ENABLED = False
DEFAULT_DIAGNOSTIC_MODE = False

# ==============================================================================
# ARDUINO & HARDWARE INTEGRATION
# ==============================================================================

# Varsayılan başlangıç denetleyici modu ("SIMULATION" veya "ARDUINO")
DEFAULT_CONTROLLER_MODE = "SIMULATION"

# Serial bağlantı ayarları
ARDUINO_SERIAL_PORT = "COM7"
ARDUINO_BAUDRATE = 115200

# Servo mekanik açı sınırları (Derece)
# AÇIK = SERVO_MIN_DEG, KAPALI = SERVO_MAX_DEG
SERVO_MIN_DEG = 0
SERVO_MAX_DEG = 180   # Fiziksel mekanik tam kapanma için ihtiyaç duyulan açı

# ==============================================================================
# PARMAK BAZLI KALİBRASYON
# ==============================================================================
# Her parmak için ayrı AÇIK (min) ve KAPALI (max) açı tanımlayabilirsiniz.
# Sıra: [Başparmak, İşaret, Orta, Yüzük, Serçe]
#
# Örnek: Başparmak 0→150, diğerleri 0→180 ise:
#   SERVO_FINGER_MIN = [0,   0,   0,   0,   0  ]
#   SERVO_FINGER_MAX = [150, 180, 180, 180, 180 ]
#
# BAŞLANGIÇ: Hepsini aynı tutun, mekanik teste göre ince ayar yapın.
SERVO_FINGER_MIN = [0,   0,   0,   0,   0  ]
SERVO_FINGER_MAX = [180, 180, 180, 180, 180]

# Güvenlik: Tek bir pakette (frame) bir servo en fazla kaç derece hareket edebilir?
# Ani zıplamaları engelleyerek mekanik hasarı önler. (0 = limit yok)
SERVO_MAX_STEP_DEG = 0

# Servo pin atamaları (Arduino tarafında kullanılacak referans sıra)
# Sıra: [Thumb, Index, Middle, Ring, Pinky]
SERVO_PINS = [3, 5, 6, 9, 10]

# Servo invert ayarı (Her parmak için motorun fiziksel dönüş yönünü ters çevirir)
# Varsayılan: OPEN = min°, CLOSED = max°
SERVO_INVERT = [False, False, False, False, False]

# Başlangıç ve Nötr pozisyon açıları
# Sistem ilk açıldığında veya bağlantı koptuğunda bu açılara dönülür.
SERVO_NEUTRAL_ANGLES = [0, 0, 0, 0, 0]
