/*
  Bionic Hand v3 - Sadelestirilmis versiyon
  
  HAZIR mesajini her saniye gonderir.
  S,a1,a2,a3,a4,a5 formatinda servo komutlarini alir.
*/

#include <Servo.h>

const int BAUD_RATE  = 115200;
const int NUM_SERVOS = 5;
const int SERVO_PINS[NUM_SERVOS] = {3, 5, 6, 9, 10};

Servo servos[NUM_SERVOS];
int currentAngles[NUM_SERVOS];
unsigned long lastPrint = 0;
unsigned long lastPacket = 0;

void setup() {
  Serial.begin(115200);
  delay(500); // Serial'in baslamasi icin bekle
  Serial.println("SETUP BASLADI");
  
  // Servolari birer birer baslat
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(SERVO_PINS[i]);
    currentAngles[i] = 0;
    servos[i].write(0);
    delay(100);
    Serial.print("Servo ");
    Serial.print(i);
    Serial.println(" baglandi");
  }
  
  lastPacket = millis();
  Serial.println("HAZIR - Her saniye mesaj gonderiyorum");
}

void loop() {
  // Her saniye heartbeat gonder
  if (millis() - lastPrint > 1000) {
    Serial.println("BEKLIYORUM...");
    lastPrint = millis();
  }
  
  // Veri geldiyse isle
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    Serial.print(">> ");
    Serial.println(line);
    
    if (line.startsWith("S,")) {
      String data = line.substring(2);
      int angles[NUM_SERVOS];
      int count = 0;
      
      while (data.length() > 0 && count < NUM_SERVOS) {
        int comma = data.indexOf(',');
        String token;
        if (comma == -1) {
          token = data;
          data = "";
        } else {
          token = data.substring(0, comma);
          data  = data.substring(comma + 1);
        }
        angles[count++] = token.toInt();
      }
      
      if (count == NUM_SERVOS) {
        for (int i = 0; i < NUM_SERVOS; i++) {
         const int angle = constrain(angles[i], 0, 180);
          servos[i].write(angle);
          currentAngles[i] = angle;
        }
        Serial.println("OK");
      } else {
        Serial.print("HATA: ");
        Serial.print(count);
        Serial.println("/5 deger");
      }
      lastPacket = millis();
    }
  }
  
  // 3 saniye veri gelmezse 0'a don
  if (millis() - lastPacket > 3000) {
    for (int i = 0; i < NUM_SERVOS; i++) {
      servos[i].write(0);
      currentAngles[i] = 0;
    }
    lastPacket = millis();
  }
}
