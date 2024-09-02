#include <Arduino.h>
#include "motor.h"
#include "defs.h"

motor::motor() {
  // switch(type) {
  //   case FL:
  //     pinMode(ENA_1, OUTPUT);
  //     pinMode(PIN_IN1_1, OUTPUT);
  //     pinMode(PIN_IN2_1, OUTPUT);
  //     break;
  //   case FR:
  //     pinMode(ENB_1, OUTPUT);
  //     pinMode(PIN_IN3_1, OUTPUT);
  //     pinMode(PIN_IN4_1, OUTPUT);
  //     break;
  //   case BL:
  //     pinMode(ENA_2, OUTPUT);
  //     pinMode(PIN_IN1_2, OUTPUT);
  //     pinMode(PIN_IN2_2, OUTPUT);
  //     break;
  //   case BR:
  //     pinMode(ENB_2, OUTPUT);
  //     pinMode(PIN_IN3_2, OUTPUT);
  //     pinMode(PIN_IN4_2, OUTPUT);
  //     break;
  // }
  
}

void motor::begin() {
  for (int i = 37; i <= 49; i++) pinMode(i, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);

  pinMode(14, OUTPUT);
  pinMode(15, OUTPUT);
  digitalWrite(14, HIGH);
  digitalWrite(15, HIGH);
}

void motor::tick() {
  if (!moveLoopRunning) return;

  int X = SPEED * (millis() - tmr)/1000;
  if (dir == Backward) {
    X = -X;
  }
  currentX = startX + X;
  Serial.println(currentX);

  if (currentX == targetX) {
    Serial.println("STOP");
    go(Stop);
    moveLoopRunning = false;
    return;
  }
  go(dir);
}

void motor::run(int x, int y) {
  targetX = x;
  targetY = y;

  if (targetX > currentX) dir = Forward;
  else dir = Backward;

  startX = currentX;

  // targetTime = round(abs(targerX) / SPEED);
  // Serial.println(targetTime);

  tmr = millis();
  moveLoopRunning = true;

}

void motor::setSpeed(int speed, Type type) {
  switch(type) {
    case FL:
      analogWrite(ENA_1, speed);
      break;
    case FR:
      analogWrite(ENB_1, speed);
      break;
    case BL:
      analogWrite(ENA_2, speed);
      break;
    case BR:
      analogWrite(ENB_2, speed);
      break;
    case ALL:
      analogWrite(ENB_2, speed);
      analogWrite(ENA_2, speed);
      analogWrite(ENB_1, speed);
      analogWrite(ENA_1, speed);
      break;
  }
}

void motor::go(Move _move) {
  move = _move;
  switch(move) {
    case Forward:
      motor_run(FL, B);
      motor_run(FR, B);
      motor_run(BL, B);
      motor_run(BR, B);
      break;

    case Backward:
      motor_run(FL, F);
      motor_run(FR, F);
      motor_run(BL, F);
      motor_run(BR, F);
      break;

    case Right:
      motor_run(FL, F);
      motor_run(FR, B);
      motor_run(BL, B);
      motor_run(BR, F);
      break;

    case Left:
      motor_run(FL, B);
      motor_run(FR, F);
      motor_run(BL, F);
      motor_run(BR, B);
      break;

    case Rotate:
      motor_run(FL, F);
      motor_run(FR, B);
      motor_run(BL, F);
      motor_run(BR, B);
      break;

    case Stop:
      motor_run(FL, S);
      motor_run(FR, S);
      motor_run(BL, S);
      motor_run(BR, S);
      break;
  }
}

void motor::motor_run(Type motor, Direction dir) {
  int dir1, dir2;
  switch(dir) {
    case F:
      dir1 = HIGH;
      dir2 = LOW;
      break;
    case B:
      dir1 = LOW;
      dir2 = HIGH;
      break;
    case S:
      dir1 = LOW;
      dir2 = LOW;
      break;
  }

  switch(motor) {
    case FL:
      // Serial.println("FL");
      digitalWrite(PIN_IN1_1, dir1);
      digitalWrite(PIN_IN2_1, dir2);
      break;
    case FR:
      // Serial.println("FR");
      digitalWrite(PIN_IN3_1, dir1);
      digitalWrite(PIN_IN4_1, dir2);
      break;
    case BL:
      // Serial.println("BL");
      digitalWrite(PIN_IN1_2, dir1);
      digitalWrite(PIN_IN2_2, dir2);
      break;
    case BR:
      // Serial.println("BR");
      digitalWrite(PIN_IN3_2, dir1);
      digitalWrite(PIN_IN4_2, dir2);
      break;
  }
}