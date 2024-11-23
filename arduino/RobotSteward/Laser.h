#ifndef ADUINO_LASER_H
#define ADUINO_LASER_H

#include <Arduino.h>
#include "Adafruit_VL53L0X.h"
#include <Multiservo.h>

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
  // Laser(Multiservo* _servo, Adafruit_VL53L0X* _lox, L _type) {
  Laser(Multiservo* _servo, Adafruit_VL53L0X* _lox) {
    servo = _servo;
    // type = _type;
    lox = _lox;
  }
  void begin() {
    int pin;
    // servo->attach(9);
    servo->write(60);
  }
  void scanStart() {
    lox->startRangeContinuous();
    dir = 1;
    if (currentAngle >= right) dir = -1;
  }
  void scanStop() {
    // Serial.println("Debug 2");
    lox->stopRangeContinuous();
    dir = 0;
  }
  void tick() {
    if (dir == 0) return;
    // Serial.println(millis() - lastTick);
    if (millis() - lastTick < 20) return;
    lastTick = millis();

    if (lox->isRangeComplete()) {
      dist = lox->readRange();
    }

    // Остановка на цели с задержкой
    if (dist < 250 && !isObject) { status = true; return; }
    // if (dist >= 250 && isObject) { isObject = false; delayStop = 0; release = true; }
    // if (dist < 250 && !isObject && delayStop == 0) { delayStop = millis(); isObject = false; }
    // if (dist < 250 && !isObject && delayStop >= 500) isObject = true;

    // Возобновление движения с задержкой
    // if (release && delayRelease == 0) delayRelease = millis();
    // if (release && delayRelease >= 500) { delayRelease = 0; release = false; }
    // if (release) { status = false; return; }

    if (dir == 1) {
      currentAngle += 5;
      if (currentAngle >= right) dir = -1;
    } else {
      currentAngle -= 5;
      if (currentAngle <= left) dir = 1;
    }

    servo->write(currentAngle);
    // status = true;
    Serial.println(dist);
  }

  bool status = true;
private:
  // L type;
  Multiservo* servo;
  Adafruit_VL53L0X* lox;
  VL53L0X_RangingMeasurementData_t measure;
  static const int left = 30;
  static const int right = 90;

  unsigned long lastTick = 0, delayStop = 0, delayRelease = 0;
  bool isObject = false, release = false;
  int dir = 0, currentAngle = 60;
  int dist;
};

#endif  //ADUINO_LASER_H