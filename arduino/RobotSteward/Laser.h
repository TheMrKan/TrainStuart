#ifndef ADUINO_LASER_H
#define ADUINO_LASER_H

#include <Arduino.h>
#include "Adafruit_VL53L0X.h"
#include <Multiservo.h>
#include "ContinuousDetector.h"

// enum L {
//   FRONT,
//   BACK
// };
/* side
 * 1 - left
 * 2 - center
 * 3 - right
*/

class Laser {
public:
  Laser(Multiservo* _servo, Adafruit_VL53L0X* _lox, int _pin) {
    servo = _servo;
    pin = _pin;
    lox = _lox;
  }

  void begin() {
    servo->write(60);
    servo->detach();
  }
  void scanStart() {
    servo->attach(pin);
    lox->startRangeContinuous(100);
    detector.reset();
    dir = 1;
    if (currentAngle >= right) dir = -1;
  }
  void scanStop() {
    servo->write(60);
    servo->detach();
    lox->stopRangeContinuous();
    detector.reset();
    dir = 0;
  }
  void tick() {
    if (dir == 0) return;

    if (millis() - lastTick < 40) return;
    lastTick = millis();

    if (lox->isRangeComplete()) {
      dist = lox->readRangeResult();

      isObject = dist > 0 && dist < 1500;
      detector.tick(isObject);
      if (isObject) {
        Serial.println(String(dist) + " " + String(detector.state));
      }
    }

    if (detector.state == WAITING) {
      if (dir == 1) {
        currentAngle = min(right, currentAngle + 0);
        if (currentAngle >= right) dir = -1;
      } else {
        currentAngle = max(left, currentAngle - 0);
        if (currentAngle <= left) dir = 1;
      }
      servo->write(currentAngle);
    }
    
  }

  bool status = true;
private:
  // L type;
  Multiservo* servo;
  Adafruit_VL53L0X* lox;
  int pin;
  VL53L0X_RangingMeasurementData_t measure;
  static const int left = 30;
  static const int right = 90;
  ContinuousDetector detector = ContinuousDetector(50, 500);

  unsigned long lastTick = 0, delayStop = 0, delayRelease = 0;
  bool isObject = false, release = false;
  int dir = 0, currentAngle = 60;
  uint16_t dist;
};

#endif  //ADUINO_LASER_H