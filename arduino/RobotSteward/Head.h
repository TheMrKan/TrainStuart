//
// Created by Nikit on 22.08.2024.
//

#ifndef ADUINO_HEAD_H
#define ADUINO_HEAD_H
#include <Arduino.h>

#include <Multiservo.h>
#include "defs.h"
#include "Adafruit_VL53L1X.h"

class Head {
public:
  Head(Multiservo* _servo, Multiservo* _brake, Adafruit_VL53L1X* loxHead);
  uint16_t getDistance();
  void begin();
  void home();
  void tick();

  void rotate(int x, int y);
  void rotateX(int x);
  void rotateXInf(int _dir);
  void rotateY(int y);
  void stop();

  bool isCompleted();
  int currentX = 0, sendY = 0, currentY = 40;  // Текущие углы
private:
  void tickX();
  void tickY();
  Multiservo* servo;
  Multiservo* brake;
  Adafruit_VL53L1X* loxHead;
  int servoHeadPin = 11;

  bool headLoopRunning = false, servoLoopRunning = false;
  bool stateX = false, stateY = false;
  bool endFlag = false, dir, dirY, awaitFlag = false;
  bool deltaSign = false;

  unsigned long tmrY;

  int targetX = 0, targetY = 0;  // Будущее положение
  int counterY;
  byte power = 255;

  const float angleTicks = MAX_TICK / (float)(headInputRight + abs(headInputLeft));
  const int step_marker = 90;

  void zero();
  void brakeF(bool state);
  bool isEnd() {
    return !digitalRead(END_CAP);
  }

  static void isr();
};


#endif  //ADUINO_HEAD_H