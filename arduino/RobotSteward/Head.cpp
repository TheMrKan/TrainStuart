//
// Created by Nikit on 22.08.2024.
//

#include "Head.h"
#include <Arduino.h>

#include <Multiservo.h>

#include "defs.h"
#include <EncButton.h>
EncButton enc(CLK, DT);

Head::Head(Multiservo* _servo, Multiservo* _brake) {
    servo = _servo;
    brake = _brake;
}

static void Head::isr() {
  enc.tickISR();
}

void Head::begin() {
    pinMode(45, OUTPUT);
    pinMode(47, OUTPUT);
    pinMode(49, OUTPUT);
    pinMode(22, INPUT_PULLUP);

    attachInterrupt(0, isr, CHANGE);
    attachInterrupt(1, isr, CHANGE);
    enc.setEncISR(true);

    analogWrite(EN_Head, power);
    brake->write(60);
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

  // if (currentY+counterY == targetY) {
  if ((dirY && (currentY+counterY >= targetY)) || (!dirY && (currentY+counterY <= targetY))) {
    currentY = targetY;
    stateY = true;
    servoLoopRunning = false;

    brake->write(60);
    servo->detach();
    return;
  }

  if (millis() - tmrY > 2) {
    tmrY = millis();
    int delta = abs(targetY - currentY+counterY);
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

    servo->write(currentY+counterY);
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

    if (currentX == x) {
      stateX = true;
      return;
    }
    
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
    if (y > 20) y = 20;
    if (y < -10) y = -10;
    
    if (y == 0) targetY = HeadCenter;
    else targetY = map(y, headInputDown, headInputUp, HeadDown, HeadUp);

    if (targetY - currentY > 0) dirY = true;
    else dirY = false;
    counterY = 0;

    // Serial.println("ABS inputAngle: " + String(y) + " lastAngle " + String(currentY) + " outputAngle: " + String(targetY) + " dir " + String(dirY));
    // current = target;

    tmrY = millis();
    servoLoopRunning = true;
    servo->attach(7);
    brake->write(80);
}

void Head::stop() {
  digitalWrite(PIN_IN1_head, LOW);
  digitalWrite(PIN_IN2_head, LOW);

  stateX = true;
  headLoopRunning = false;

  currentX += round(-enc.counter / angleTicks);
  enc.counter = 0;
}

bool Head::getState(char axis) {
  if (axis == 'x') {
    if (stateX) {
      stateX = false;
      return true;
    }
    return false;
  } else {
    if (stateY) {
      stateY = false;
      return true;
    }
    return false;
  }
}