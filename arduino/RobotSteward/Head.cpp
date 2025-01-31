//
// Created by Nikit on 22.08.2024.
//

#include "Head.h"
#include <Arduino.h>

#include <Multiservo.h>

#include "defs.h"
#include <EncButton.h>
EncButton enc(CLK, DT);

const int INF = 1000;

Head::Head(Multiservo* _servo, Multiservo* _brake, Adafruit_VL53L1X* _loxHead) {
  servo = _servo;
  brake = _brake;
  loxHead = _loxHead;
}

uint16_t Head::getDistance() {
  if (loxHead->dataReady()) {
    int16_t distance = loxHead->distance();
    if (distance == -1) {
      // something went wrong!
      Serial.print(F("Couldn't get distance: "));
      Serial.println(loxHead->vl_status);
      return 0;
    }

    loxHead->clearInterrupt();
    return distance;
  }
  else {
    // Serial.println("Distance data is not ready");
    return 0;
  }
}

static void Head::isr() {
  enc.tickISR();
}

void Head::begin() {
  pinMode(45, OUTPUT);
  pinMode(47, OUTPUT);
  pinMode(49, OUTPUT);
  pinMode(22, INPUT_PULLUP);
  pinMode(HEAD_MARKER, INPUT);

  attachInterrupt(0, isr, CHANGE);
  attachInterrupt(1, isr, CHANGE);
  enc.setEncISR(true);

  analogWrite(EN_Head, power);
  brake->write(60);
  brake->detach();
}

void Head::tick() {
  tickX();
  tickY();
}

bool isHeadMarker() {
  return analogRead(HEAD_MARKER) > 1000;
}

/*
  Если при вызове команды "Hi 1" голова поворачивается в крайний угол (158), 
  то после повторного вызова этой же функции назад он не поедет (потому что текущий угол не перзаписывается)
*/
void Head::tickX() {
  enc.tick();
  

  if (isEnd()) {
    if (!endFlag) {
      currentX = headInputLeft;
      endFlag = true;
    } else endFlag = false;
  }

  if (!headLoopRunning) return;

  // Serial.println(-enc.counter);
  int _currentX = currentX + round(-enc.counter / angleTicks);

  if (isHeadMarker()) {
     
     enc.counter = 0;
     const int angle = round((float)_currentX / (float)HEAD_MARKER_STEP) * HEAD_MARKER_STEP;
     // Serial.println("HEAD MARKER " + String(angle) + " " + String((float)_currentX / (float)HEAD_MARKER_STEP) + " " + String(_currentX));
     _currentX = angle;
     currentX = angle;
   }

  if ((!dir && isEnd()) || (dir && _currentX >= (headInputRight - 2))) {
    // Serial.println(currentX);
    stop();
    return;
  }

  int delta = targetX - _currentX;
  int localPower = power;

  if (abs(targetX) == INF) {
    localPower = power / 2;
  } else if (abs(delta) < 2) {
    localPower = power / 3;
  } else if (abs(delta) < 10) {
    localPower = power / 2;
  }

  if (abs(targetX) != INF && ((delta > 0) != deltaSign || delta == 0)) {
    stop();
    // Serial.println(currentX);
    return;
  }
  // Serial.println(deltaSign);
  deltaSign = targetX - _currentX > 0;
  digitalWrite(PIN_IN1_head, dir ? HIGH : LOW);
  digitalWrite(PIN_IN2_head, dir ? LOW : HIGH);

  stateX = false;
  analogWrite(EN_Head, localPower);
  // Serial.println(_currentX);
}

void Head::tickY() {
  if (!servoLoopRunning) return;

  // if (currentY+counterY == targetY) {
  if ((dirY && (currentY + counterY >= targetY)) || (!dirY && (currentY + counterY <= targetY))) {
    currentY = targetY;
    stateY = true;
    servoLoopRunning = false;

    servo->detach();
    brakeF(true);
    return;
  }

  if (millis() - tmrY > 75) {
    tmrY = millis();
    int delta = abs(targetY - currentY + counterY);
    int absStep;

    // if (delta > 50)
    //     absStep = 10;
    // else if (delta > 10 && delta <= 50)
    //     absStep = 2;

    if (delta > 10) absStep = 5;
    else if (delta <= 10 && delta > 5) absStep = 2;
    else absStep = 1;

    if (dirY) counterY += absStep;
    else counterY -= absStep;

    servo->write(currentY + counterY);
    // Serial.println(String(currentY+counterY) + " Step: " + String(absStep));
  }
  stateY = false;
}

void Head::zero() {
  if (isEnd()) {
    currentX = headInputLeft;
    endFlag = true;
    return;
  }

  analogWrite(EN_Head, power);
  while (!isEnd()) {
    digitalWrite(PIN_IN1_head, LOW);
    digitalWrite(PIN_IN2_head, HIGH);
  }
  enc.counter = 0;
  digitalWrite(PIN_IN1_head, LOW);
  digitalWrite(PIN_IN2_head, LOW);

  currentX = headInputLeft;
  endFlag = true;
}

void Head::brakeF(bool state) {
  if (state) {
    brake->attach(8);
    brake->write(60);
    delay(500);
    brake->detach();
  } else {
    brake->attach(8);
    brake->write(80);
    delay(500);
    brake->detach();
  }
}

void Head::home() {
  zero();
  rotate(0, 0);
}

void Head::rotate(int x, int y) {
  rotateX(x);
  rotateY(y);
}

void Head::rotateX(int x) {
  if (x > 160) x = 160;
  if (x < -165) x = -165;

  if (abs(currentX - x) <= 2) {
    stateX = true;
    return;
  }

  currentX += round(-enc.counter / angleTicks);
  targetX = x;
  enc.counter = 0;
  deltaSign = targetX - currentX > 0;

  dir = deltaSign;

  // awaitFlag = false;
  headLoopRunning = true;
}

void Head::rotateXInf(int _dir) {
  if (_dir == 0) {
    stop();
    return;
  }
  stateX = false;
  stateY = true;

  Serial.println("Head rotation inf: dir - " + String(_dir) + "; currentX - " + String(currentX));

  dir = _dir > 0;
  enc.counter = 0;
  targetX = INF;
  headLoopRunning = true;
}

void Head::rotateY(int y) {
  if (y > 30) y = headInputUp;
  if (y < -10) y = headInputDown;

  if (y == 0) targetY = HeadCenter;
  if (y > 0) targetY = map(y, headInputCenter, headInputUp, HeadCenter, HeadUp);
  else targetY = map(y, headInputCenter, headInputDown, HeadCenter, HeadDown);

  if (abs(targetY - currentY) <= 2) {
    stateY = true;
    return;
  }

  if (targetY > currentY) dirY = true;
  else dirY = false;
  counterY = 0;
  sendY = y;

  // Serial.println("ABS inputAngle: " + String(y) + " lastAngle " + String(currentY) + " outputAngle: " + String(targetY) + " dir " + String(dirY));
  // current = target;
  tmrY = millis();
  servoLoopRunning = true;
  brakeF(false);
  servo->attach(servoHeadPin); // 7
}

void Head::stop() {
  digitalWrite(PIN_IN1_head, LOW);
  digitalWrite(PIN_IN2_head, LOW);

  stateX = true;
  headLoopRunning = false;

  currentX += round(-enc.counter / angleTicks);
  enc.counter = 0;
}

bool Head::isCompleted() {
  // if (stateX || stateY) {
  //   Serial.println("State head: " + String(stateX) + " " + String(stateY));
  // }

  if (stateX && stateY) {
    stateX = false;
    stateY = false;
    return true;
  }
  return false;
}