//
// Created by Nikit on 22.08.2024.
//

#ifndef ADUINO_HEAD_H
#define ADUINO_HEAD_H
#include <Arduino.h>

#include <Multiservo.h>
#include "defs.h"


class Head {
public:
  Head(Multiservo* _servo, Multiservo* _brake);
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
  bool headLoopRunning = false, servoLoopRunning = false;
  bool stateX = false, stateY = false;

  unsigned long tmrY;

  bool endFlag = false, dir, dirY, awaitFlag = false;
  bool deltaSign = false;

  int targetTickX = 0, targetY = 0;  // Будущее положение

  const float angleTicks = MAX_TICK / (float)(headInputRight + abs(headInputLeft));
  int counterY;

  byte power = 255;
  int servoHeadPin = 11;

  void zero();
  void brakeF(bool state);
  bool isEnd() {
    return !digitalRead(END_CAP);
  }

  static void isr();
};


#endif  //ADUINO_HEAD_H