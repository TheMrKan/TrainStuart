//
// Created by Nikit on 22.08.2024.
//

#include "Head.h"
#include <Arduino.h>

#include <Multiservo.h>

#include "defs.h"
#include <EncButton.h>
EncButton enc(CLK, DT);

Head::Head(Multiservo* _servo) {
    servo = _servo;
}

static void Head::isr() {
  enc.tickISR();
}

void Head::begin() {
    pinMode(45, OUTPUT);
    pinMode(47, OUTPUT);
    pinMode(49, OUTPUT);
    pinMode(22, INPUT_PULLUP);

//    servo.attach(7);
    attachInterrupt(0, isr, CHANGE);
    attachInterrupt(1, isr, CHANGE);
    enc.setEncISR(true);

    analogWrite(EN_Head, power);
}

// void Head::tick() {
//     enc.tick();
//     if (isEnd()) {
//       if (!endFlag) {
//         currentX = headInputLeft;
//         endFlag = true;
//       } else endFlag = false;
//     }

//     if (!headLoopRunning) return;

//     if ((-enc.counter - targetTickX > 0) != deltaSign) {
//         stop();
//         return;
//     }
//     deltaSign = -enc.counter - targetTickX > 0;

//     digitalWrite(PIN_IN1_head, dir ? HIGH : LOW);
//     digitalWrite(PIN_IN2_head, dir ? LOW : HIGH);

//     stateX = false;
//     analogWrite(EN_Head, power);
// }
void Head::tick() {
  tickX();
  tickY();
}

void Head::tickX() {
    enc.tick();
    if (isEnd()) {
      if (!endFlag) {
        currentX = headInputLeft;
        endFlag = true;
      } else endFlag = false;
    }

    if (!headLoopRunning) return;

    if ((-enc.counter - targetTickX > 0) != deltaSign) {
        stop();
        return;
    }
    deltaSign = -enc.counter - targetTickX > 0;
    digitalWrite(PIN_IN1_head, dir ? HIGH : LOW);
    digitalWrite(PIN_IN2_head, dir ? LOW : HIGH);

    stateX = false;
    analogWrite(EN_Head, power);
}

void Head::tickY() {
  if (!servoLoopRunning) return;

  // if ()
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

void Head::home() {
    zero();
    rotate(0, 0);
}

void Head::rotate(int x, int y) {
    rotateX(x);
    rotateY(y);
}

void Head::rotateX(int x) {
    currentX += round(-enc.counter / angleTicks);
    int targetAngle = x - currentX;
    enc.counter = 0;
    targetTickX = round(targetAngle * angleTicks);
    deltaSign = -enc.counter - targetTickX > 0;


    if (targetTickX < 0) dir = false;
    else dir = true;

    // awaitFlag = false;
    headLoopRunning = true;
}

void Head::rotateY(int y) {
    if (y == 0) targetY = HeadCenter;
    else targetY = map(y, headInputDown, headInputUp, HeadDown, HeadUp);

    countY = currentY - targetY;
    servoLoopRunning = true;
    servo->write(targetY);
}

void Head::stop() {
  digitalWrite(PIN_IN1_head, LOW);
  digitalWrite(PIN_IN2_head, LOW);

  stateX = true;
  headLoopRunning = false;

  currentX += round(-enc.counter / angleTicks);
  enc.counter = 0;
}

bool Head::getState() {
    if (stateX) {
      stateX = false;
      return true;
    }
    return false;
}