<div align="center">

# 🦾 Biyonik El — Bionic Hand Control System

### Real-Time Hand Gesture Recognition & Arduino Servo Control

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10%2B-FF6F00?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-00979D?style=for-the-badge&logo=arduino&logoColor=white)](https://arduino.cc)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**[Türkçe](#-proje-hakkında) · [English](#-about-the-project)**

</div>

---

## 📖 Proje Hakkında

Bu proje, bilgisayar kamerasından insan elinin hareketlerini **gerçek zamanlı** olarak algılayan ve bu hareketleri **Arduino tabanlı 5 servolu biyonik eli** kontrol etmek için kullanan modüler bir Python + Arduino sistemidir.

- 🎯 **Webcam** ile elinizi kameraya gösterin
- 🧠 **MediaPipe AI** 21 el landmarkını milisaniyeler içinde tespit eder
- ⚙️ **Motion Engine** ham veriyi filtreler, yumuşatır ve servo açılarına dönüştürür
- 🤖 **Arduino** 5 servo motoru gerçek zamanlı kontrol eder
- 📊 **Diagnostic Panel** ile tüm veriyi canlı izleyin

---

## 📖 About the Project

This project is a modular Python + Arduino system that detects human hand movements in **real-time** using a computer camera and uses them to control an **Arduino-based 5-servo bionic hand**.

- 🎯 Show your hand to the **webcam**
- 🧠 **MediaPipe AI** detects 21 hand landmarks within milliseconds
- ⚙️ **Motion Engine** filters, smooths, and converts raw data into servo angles
- 🤖 **Arduino** controls 5 servo motors in real-time
- 📊 Monitor all data live with the **Diagnostic Panel**

---

## 🏗️ Sistem Mimarisi / System Architecture

```
Webcam (1280×720)
      │
      ▼
┌─────────────────────┐
│   Hand Detector     │  MediaPipe HandLandmarker → 21 Landmark Noktası
│   (hand_detector)   │  Güven eşiği: %70 tespit, %60 takip
└──────────┬──────────┘
           │  HandState (5 parmak + normalize değerler)
           ▼
┌─────────────────────┐
│  Gesture Detector   │  OPEN_HAND · FIST · POINT · PEACE · THUMBS_UP · PINCH
│ (gesture_detector)  │  5-frame debounce → Stabil jest tanıma
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Motion Mapper     │  Per-parmak kalibrasyon (input_min/max → output_min/max)
│  (motion_mapper)    │  Kullanıcıya özel ayar desteği
└──────────┬──────────┘
           │  Ham BionicHandState [0.0 – 1.0]
           ▼
┌─────────────────────┐
│ BionicHandSmoother  │  EMA Smoothing (α=0.6) + Dead Zone (%2) + Hand Lost → HOLD_LAST
│    (smoother)       │
└──────────┬──────────┘
           │  Yumuşatılmış BionicHandState → Servo Açıları [0° – 90°]
           ▼
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌───────┐   ┌──────────────┐
│ SIM   │   │   ARDUINO    │  S,angle1,angle2,angle3,angle4,angle5 protokolü
│ MODE  │   │  (COM7 @     │  115200 baud · 5 servo · PWM pinleri: 3,5,6,9,10
└───────┘   │  115200 baud)│
            └──────────────┘
           │
           ▼
┌─────────────────────┐
│    Visualizer       │  HUD + 2D El Animasyonu + Progress Bar + Diagnostic Panel
│   (bionic_viz)      │
└─────────────────────┘
```

---

## 📁 Proje Yapısı / Project Structure

```
biyonik_el/
│
├── 📂 src/                          # Python kaynak kodları
│   ├── main.py                      # ← Ana uygulama, buradan başlatın
│   ├── config.py                    # Tüm ayarlar tek bir yerde (baud rate, pin, alpha, vb.)
│   ├── camera.py                    # Webcam açma/okuma/FPS yönetimi
│   ├── hand_detector.py             # MediaPipe HandLandmarker entegrasyonu
│   ├── hand_state.py                # HandState ve FingerState veri yapıları
│   ├── finger_state.py              # Parmak geometri analizi (vektör açısı)
│   ├── gesture_detector.py          # Gesture tanıma + debounce algoritması
│   ├── motion_mapper.py             # Parmak kalibrasyon ve eşleme motoru
│   ├── smoother.py                  # EMA smoothing + dead zone + hand lost
│   ├── bionic_hand_state.py         # BionicHandState veri yapısı
│   ├── simulation.py                # Yazılım simülasyon kontrolcüsü
│   ├── arduino_controller.py        # Arduino & Mock Arduino kontrolcüsü
│   ├── visualizer.py                # HandState HUD görselleştirmesi
│   ├── bionic_visualizer.py         # BionicPanel + 2D El + DiagnosticPanel
│   └── data_logger.py               # CSV veri kayıt sistemi
│
├── 📂 arduino/
│   └── bionic_hand/
│       └── bionic_hand.ino          # ← Arduino'ya yüklenecek firmware
│
├── 📂 models/
│   └── hand_landmarker.task         # MediaPipe AI modeli (otomatik indirilir)
│
├── 📂 tests/
│   ├── test_logic.py                # Birim testler (Motion Engine, Gesture, Dead Zone)
│   └── test_arduino.py              # Arduino haberleşme protokol testleri
│
├── 📂 logs/                         # CSV log dosyaları (L tuşuyla kaydedilir)
├── test_webcam.py                   # 8 saniyelik otomatik webcam testi
├── requirements.txt                 # Python bağımlılıkları
└── .gitignore
```

---

## ⚡ Hızlı Başlangıç / Quick Start

### Ön Gereksinimler / Prerequisites

| Gereksinim | Sürüm | Notlar |
|---|---|---|
| **Python** | 3.10 veya üzeri | [python.org](https://python.org) adresinden indirin |
| **Webcam** | Herhangi bir USB/dahili kamera | 720p veya üzeri önerilir |
| **Arduino IDE** | 2.0+ (isteğe bağlı) | Sadece fiziksel Arduino kullanacaksanız |
| **Arduino Uno** | R3 veya uyumlu | Sadece gerçek donanım için |
| **5× Servo Motor** | SG90 veya MG90S | 0°–90° hareket aralığı |

---

### 🖥️ Adım 1 — Python Kurulumu

**Windows için:**

```bash
# 1. Repoyu klonlayın
git clone https://github.com/IEEE-ORGU/biyonik_el.git
cd biyonik_el

# 2. Sanal ortam oluşturun (şiddetle önerilir)
python -m venv venv

# 3. Sanal ortamı aktive edin
venv\Scripts\activate

# 4. Bağımlılıkları yükleyin
pip install -r requirements.txt
```

**Linux / macOS için:**

```bash
git clone https://github.com/IEEE-ORGU/biyonik_el.git
cd biyonik_el

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

> **📝 Not:** Eğer `venv\Scripts\activate` çalıştırırken PowerShell'de hata alırsanız:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### 🤖 Adım 2 — MediaPipe Modelini İndirin

```bash
# models/ klasörüne gidin ve modeli indirin
python -c "
import urllib.request, os
os.makedirs('models', exist_ok=True)
url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'
print('Model indiriliyor...')
urllib.request.urlretrieve(url, 'models/hand_landmarker.task')
print('Tamamlandı!')
"
```

> **💡 İpucu:** Model zaten `models/` klasöründe varsa bu adımı atlayabilirsiniz.

---

### ▶️ Adım 3 — Uygulamayı Çalıştırın

```bash
# Sanal ortamın aktif olduğundan emin olun
venv\Scripts\activate  # Windows
# veya
source venv/bin/activate  # Linux/macOS

# Uygulamayı başlatın
python src\main.py
```

Uygulama başladığında terminalde şunu görmelisiniz:

```
============================================================
  BIYONIK EL -- El Hareketi Tanima (Teslimat 4)
============================================================
  Smoothing alpha    : 0.6
  Dead zone          : 0.02
  Kontroller:
    [D] Diagnostic Mode Aç/Kapat
    [L] Logging Aç/Kapat
    [R] Smoother Sifirla
    [A] Arduino Moduna Geç
    [S] Simulation Moduna Geç
    [Q] / [ESC] Cikis

  Kamera acildi: 1280x720
  El gosterin...
```

---

## ⌨️ Klavye Kısayolları / Keyboard Shortcuts

| Tuş | İşlev |
|-----|-------|
| `Q` veya `ESC` | Uygulamadan çık |
| `D` | Diagnostic (Tanılama) panelini aç/kapat |
| `L` | CSV veri kaydını başlat/durdur (`logs/` klasörüne kaydeder) |
| `R` | Smoother'ı sıfırla (ani pozisyon değişimi sonrası kullanın) |
| `A` | Arduino moduna geç (kart bağlı değilse otomatik MOCK moda düşer) |
| `S` | Simülasyon moduna geri dön |

---

## 🎯 Tanınan Jestler / Recognized Gestures

| Jest | Görsel | Açıklama |
|------|--------|----------|
| `OPEN_HAND` | ✋ | Tüm parmaklar açık |
| `FIST` | ✊ | Tüm parmaklar kapalı (yumruk) |
| `POINT` | 👆 | Sadece işaret parmağı açık |
| `PEACE` | ✌️ | İşaret + orta parmak açık |
| `THUMBS_UP` | 👍 | Sadece başparmak açık |
| `PINCH` | 🤏 | Başparmak ve işaret uçları birbirine yakın |

---

## 🔌 Arduino Donanım Kurulumu / Arduino Hardware Setup

> **⚠️ DONANIM GEREKMİYOR:** Arduino olmadan da uygulamayı çalıştırabilirsiniz. Uygulama varsayılan olarak **Simülasyon Modu**'nda başlar.

### Bağlantı Şeması / Wiring Diagram

```
Arduino Uno
┌─────────────────────────┐
│  Pin  3 (PWM) ──────────┼──→ Başparmak Servo (SIGNAL)
│  Pin  5 (PWM) ──────────┼──→ İşaret Parmağı Servo (SIGNAL)
│  Pin  6 (PWM) ──────────┼──→ Orta Parmak Servo (SIGNAL)
│  Pin  9 (PWM) ──────────┼──→ Yüzük Parmağı Servo (SIGNAL)
│  Pin 10 (PWM) ──────────┼──→ Serçe Parmağı Servo (SIGNAL)
│  GND          ──────────┼──→ Harici Güç GND + Tüm Servo GND
│  USB ───────────────────┼──→ Bilgisayar (Serial haberleşme)
└─────────────────────────┘

Harici Güç Kaynağı (5V 3A+)
    (+) ──→ Tüm Servo VCC (kırmızı kablo)
    (-) ──→ Arduino GND + Tüm Servo GND (siyah kablo) ← ORTAK TOPRAK ZORUNLU!
```

> **🔴 KRİTİK UYARI:** 5 servo motoru **ASLA** Arduino'nun 5V piniyle beslemeyin!  
> Servoların anlık akım çekimi Arduino'yu bozabilir veya USB portuna zarar verebilir.  
> **Mutlaka harici 5V 3A+ güç kaynağı kullanın ve GND'leri birleştirin!**

### Arduino Firmware Yükleme

1. [Arduino IDE](https://www.arduino.cc/en/software)'yi indirin ve kurun
2. `arduino/bionic_hand/bionic_hand.ino` dosyasını açın
3. **Tools → Board → Arduino Uno** seçin
4. **Tools → Port → COMx** (aygıt yöneticisinden kontrol edin)
5. **Upload** (→) butonuna basın

### Seri Port Ayarı

Arduino bağlandıktan sonra `src/config.py` dosyasını açın ve port ayarını güncelleyin:

```python
# src/config.py
ARDUINO_SERIAL_PORT = "COM7"   # ← Windows: COMx, Linux: /dev/ttyUSB0, macOS: /dev/tty.usbmodem*
ARDUINO_BAUDRATE    = 115200   # Arduino firmware ile aynı olmalı
```

### Arduino Haberleşme Protokolü

```
Bilgisayar → Arduino:  S,angle1,angle2,angle3,angle4,angle5\n
             Örnek:    S,45,30,60,0,90\n

Arduino → Bilgisayar:  OK        (başarılı)
                        BEKLIYORUM... (her saniye heartbeat)
                        HATA: x/5 deger (hatalı paket)
```

---

## 📊 Özellikler / Features

### ✅ Gerçek Zamanlı El Tespiti
- MediaPipe HandLandmarker ile **21 landmark** noktası tespiti
- %70 detection, %60 tracking güven eşiği
- Sol / Sağ el otomatik belirleme
- 30+ FPS performans

### ✅ Motion Engine
- **EMA Smoothing** (α=0.6): Titreşim giderme, akıcı servo hareketi
- **Dead Zone** (%2): Küçük gürültü filtresi, servo ömrünü uzatır
- **Hand Lost → HOLD_LAST**: El kaybolunca son pozisyonu koru (güvenli)
- **Per-Finger Kalibrasyon**: Her parmak için bağımsız min/max ayarı

### ✅ Gesture Tanıma
- 6 farklı jest: OPEN_HAND, FIST, POINT, PEACE, THUMBS_UP, PINCH
- **Debounce algoritması** (5-frame): Micro-titremeleri engeller

### ✅ Arduino Entegrasyonu
- Gerçek donanım + **Mock (Sahte) mod** desteği
- Heartbeat keep-alive paketi (timeout koruması)
- **Step limiti** desteği (ani servo hareketi koruması)
- Emergency Stop (bağlantı kopunca otomatik nötr pozisyon)

### ✅ Görselleştirme
- Gerçek zamanlı **2D el animasyonu**
- **Progress bar** paneli (5 parmak)
- **Diagnostic Panel**: RAW · SMOOTH · TARGET · SERVO açısı canlı gösterge

### ✅ Veri Kaydı
- `L` tuşuyla CSV formatında log kaydetme
- Her frame: timestamp, parmak değerleri, jest, FPS

---

## 🔧 Konfigürasyon / Configuration

Tüm ayarlar `src/config.py` dosyasında merkezi olarak yönetilir:

```python
# Kamera
CAMERA_INDEX  = 0       # 0 = dahili webcam, 1 = harici USB kamera
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720

# MediaPipe
MP_MAX_HANDS             = 1    # Kaç el takip edilsin
MP_DETECTION_CONFIDENCE  = 0.7  # Tespit güven eşiği
MP_TRACKING_CONFIDENCE   = 0.6  # Takip güven eşiği

# Smoothing
SMOOTHING_ALPHA = 0.6   # 0.1 (çok yavaş) → 1.0 (ham veri)
DEAD_ZONE       = 0.02  # %2 değişim filtresi

# Arduino
ARDUINO_SERIAL_PORT = "COM7"     # Bağlı port
ARDUINO_BAUDRATE    = 115200
SERVO_PINS          = [3, 5, 6, 9, 10]  # [Baş, İşaret, Orta, Yüzük, Serçe]
SERVO_MIN_DEG       = 0          # Servo minimum açı
SERVO_MAX_DEG       = 90         # Servo maksimum açı

# Gesture
GESTURE_STABILITY_FRAMES = 5    # Kaç frame aynı kalınca jest kabul edilsin
```

---

## 🧪 Testleri Çalıştırma / Running Tests

```bash
# Sanal ortamı aktive edin
venv\Scripts\activate

# Tüm birim testleri çalıştır (webcam gerekmez)
python -m pytest tests/ -v

# Sadece mantık testleri
python -m pytest tests/test_logic.py -v

# Sadece Arduino protokol testleri
python -m pytest tests/test_arduino.py -v

# 8 saniyelik webcam testi (kamera gerektirir)
python test_webcam.py
```

---

## ❓ Sık Sorulan Sorular / FAQ

<details>
<summary><b>🔴 "Kamera açılamadı" hatası alıyorum</b></summary>

- `config.py` içinde `CAMERA_INDEX = 0` değerini `1` veya `2` yapıp deneyin
- Başka bir uygulama (Zoom, Teams, vb.) kamerayı kullanıyor olabilir, kapatın
- Sanal makine (VMware/VirtualBox) kullanıyorsanız USB kamera pass-through ayarı gerekir

</details>

<details>
<summary><b>🔴 "Module not found: mediapipe" hatası</b></summary>

Sanal ortamın aktif olmadığı anlamına gelir:

```bash
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
```

</details>

<details>
<summary><b>🔴 Arduino bağlanamıyor / COM port bulunamıyor</b></summary>

1. Aygıt Yöneticisi'nde (Device Manager) Arduino'nun hangi COM portunda göründüğünü bulun
2. `config.py` içinde `ARDUINO_SERIAL_PORT = "COM7"` satırını doğru porta güncelleyin
3. Arduino IDE'nin Serial Monitor'ü açık olmamasına dikkat edin — sadece bir program aynı anda porta bağlanabilir
4. Arduino bağlı değilse `A` tuşuna bastığınızda **MOCK ARDUINO** modu devreye girer (uygulama çökmez)

</details>

<details>
<summary><b>🔴 El tespiti çok hassas / titriyor</b></summary>

`config.py` içinde şu değerleri ayarlayın:

```python
SMOOTHING_ALPHA = 0.25   # Daha düşük = daha yumuşak (önerilen: 0.15–0.35)
DEAD_ZONE       = 0.05   # Daha yüksek = daha agresif filtreleme
GESTURE_STABILITY_FRAMES = 8  # Daha yüksek = daha stabil jest tanıma
```

</details>

<details>
<summary><b>🔴 Servolar yanlış yönde dönüyor</b></summary>

`config.py` içinde ilgili parmağın invert değerini `True` yapın:

```python
SERVO_INVERT = [False, True, False, False, False]
#               Baş   İşaret Orta   Yüzük  Serçe
```

</details>

---

## 📦 Bağımlılıklar / Dependencies

| Paket | Sürüm | Amaç |
|-------|-------|------|
| `mediapipe` | ≥ 0.10.0 | 21 el landmark tespiti (AI model) |
| `opencv-python` | ≥ 4.8.0 | Kamera, görüntü işleme, HUD çizimi |
| `numpy` | ≥ 1.24.0 | Geometrik hesaplamalar, EMA smoothing |
| `pyserial` | opsiyonel | Gerçek Arduino bağlantısı için |

---

## 🤝 Katkıda Bulunma / Contributing

1. Bu repoyu **Fork** edin
2. Feature branch oluşturun: `git checkout -b feature/yeni-ozellik`
3. Değişikliklerinizi commit edin: `git commit -m "feat: yeni özellik eklendi"`
4. Branch'i push edin: `git push origin feature/yeni-ozellik`
5. **Pull Request** açın

---

## 👥 Ekip / Team

Bu proje **IEEE Ege Student Branch** bünyesinde geliştirilmiştir.

---

## 📄 Lisans / License

Bu proje MIT Lisansı ile lisanslanmıştır. Ayrıntılar için [LICENSE](LICENSE) dosyasına bakınız.

---

<div align="center">

**IEEE Ege Student Branch** tarafından ❤️ ile yapılmıştır

*El hareketleri ile biyonik kontrol — Gerçek zamanlı, modüler, açık kaynak*

</div>
