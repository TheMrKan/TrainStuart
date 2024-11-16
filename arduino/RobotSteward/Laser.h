#include <Arduino.h>

#include "Adafruit_VL53L0X.h"

#include <Multiservo.h>


/* side
 * 1 - left
 * 2 - center
 * 3 - right
*/

enum L {
  FRONT,
  BACK
};

class Laser {
  public:
    Laser(Multiservo* _servo, Adafruit_VL53L0X* _lox, L _type) {
      servo = _servo;
      type = _type;
      lox = _lox;
    }
    void begin() {
      int pin;
      servo->attach(9);
      Serial.println("Debug 0");
      servo->write(60);
      // if (!lox->begin()) {
      //   Serial.println(F("Failed to boot VL53L0X"));
      //   while(1);
      // }
      // lox->startRangeContinuous();
    }
    void scanStart() {
      lox->startRangeContinuous();
      Serial.println("Debug 1");
      dir = 1;
      if (currentAngle >= right) dir = -1;
    }
    void scanStop() {
      Serial.println("Debug 2");
      lox->stopRangeContinuous();
      dir = 0;
    }
    void tick() {
      // Serial.println("dir " + String(dir) + " lastTick " + String(lastTick));
      if (dir == 0) return;
      Serial.println(millis() - lastTick);
      if (millis() - lastTick < 20) return;
      lastTick = millis();

      if (lox->isRangeComplete()) {
        dist = lox->readRange();
      }

      if (dist < 250) return;
      if (dir == 1) {
        currentAngle += 5;
        if (currentAngle >= right) dir = -1;
      } else {
        currentAngle -= 5;
        if (currentAngle <= left) dir = 1;
      }

      servo->write(currentAngle);
    }
  private:
    L type;
    Multiservo* servo;
    Adafruit_VL53L0X* lox;
    VL53L0X_RangingMeasurementData_t measure;
    static const int left = 30;
    static const int right = 90;

    unsigned long lastTick = 0;
    int dir = 0, currentAngle = 60;
    int dist, step;
};