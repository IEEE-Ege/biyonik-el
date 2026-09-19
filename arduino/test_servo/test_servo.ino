/*
  test_servo.ino — Tek servo test kodu
  
  Sadece PIN 3'teki servoya bakıyor.
  Serial Monitor'de:
    "a" yaz → 0 derece (AÇIK)
    "k" yaz → 90 derece (KAPALI)
    "S,45,45,45,45,45" yaz → 5 servo format test
  
  LED 13 yanıp sönüyorsa kod çalışıyor.
*/

#include <Servo.h>

Servo testServo;
const int SERVO_PIN = 3;
const int LED_PIN = 13;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  
  testServo.attach(SERVO_PIN);
  testServo.write(0);   // Başlangıç: 0 derece
  
  // Hazır sinyali: 3 kez yanıp söner
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
  
  Serial.println("HAZIR. 'a'=Ac, 'k'=Kapat, S,45,... formatini dene");
}

void loop() {
  if (Serial.available() > 0) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();
    
    // LED yak — veri geldi sinyali
    digitalWrite(LED_PIN, HIGH);
    Serial.print("ALINDI: ");
    Serial.println(incoming);
    
    if (incoming == "a") {
      testServo.write(0);
      Serial.println("→ 0 derece (ACIK)");
    }
    else if (incoming == "k") {
      testServo.write(90);
      Serial.println("→ 90 derece (KAPALI)");
    }
    else if (incoming.startsWith("S,")) {
      // S,45,45,45,45,45 formatını parse et
      String vals = incoming.substring(2);
      int firstComma = vals.indexOf(',');
      int angle = vals.substring(0, firstComma).toInt();
      angle = constrain(angle, 0, 90);
      testServo.write(angle);
      Serial.print("→ Servo PIN3 = ");
      Serial.print(angle);
      Serial.println(" derece");
    }
    
    delay(100);
    digitalWrite(LED_PIN, LOW);
  }
}
