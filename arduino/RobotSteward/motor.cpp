#include <Arduino.h>
#include "motor.h"
#include "defs.h"
#include "CompassRemote.h"

motor::motor(Laser* _laserF, Laser* _laserB, CompassRemote* _compass) {
  laserF = _laserF;
  laserB = _laserB;
  compass = _compass;
}
// motor::motor() {

// }

unsigned long lastSendX = 0;

void motor::begin() {
  for (int i = 37; i <= 49; i++) pinMode(i, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);

  pinMode(14, OUTPUT);
  pinMode(15, OUTPUT);
  digitalWrite(14, HIGH);
  digitalWrite(15, HIGH);

  pinMode(A14, INPUT);
  pinMode(A15, INPUT);
}

void motor::tick() {
  tickX();
  tickY();
  tickCorrectingY();
}

void motor::tickX() {
  if (!moveXLoopRunning) return;
  if (pause) {
    go(Stop);
    return;
  }

  int X = SPEED_X * (millis() - tmr) / 1000;
  if (dir == Backward) {
    X = -X;
  }
  currentX = startX + X;


  if ((dir == Forward && (currentX >= targetX)) || (dir == Backward && (currentX <= targetX))) {
    // Serial.println("STOP " + String(currentX));
    go(Stop);
    moveXLoopRunning = false;

    completeX = true;
    completeY = true;
    return;
  }

  go(dir);
  completeX = false;
  // completeY = false;
}

void motor::tickY() {
  if (!moveYLoopRunning) return;

  float speed = dir == Right ? SPEED_Y_RIGHT : SPEED_Y_LEFT;
  int Y = speed * (millis() - tmr) / 1000;
  if (dir == Right) {
    Y = -Y;
  }
  currentY = startY + Y;
  // Serial.println("dir: " + String(dir) + " speed: " + String(speed) + " currentY: " + String(currentY) + " targetY: " + String(targetY));
  if ((dir == Left && (currentY >= targetY)) || (dir == Right && (currentY <= targetY))) {
    Serial.println("STOP " + String(currentY) + String(" ") + String(((float)millis() - tmr) / 1000));
    go(Stop);
    moveYLoopRunning = false;
    isCorrectingY = true;

    completeX = true;
    completeY = true;
    return;
  }
  go(dir);

  // completeX = false;
  completeY = false;

  // Serial.println("Dir: " + String(dir) + " currentY: " + String(currentY));
}

void motor::tickCorrectingY() {
  if (!isCorrectingY) return;

  compassData = compass->readData();
  Serial.println("DELTA: " + String(compassData.delta));

  if (abs(compassData.delta) <= 1) {
    isCorrectingY = false;
    go(Stop);
    return;
  }

  if (compassData.delta > 0) {
    go(RotateL);
  } else go(RotateR);
}

void motor::run(int x, int y) {
  // if (abs(currentX - x) >= abs(currentY - y)) runX(x);
  // else runY(y);
  // runX(x);
  if (abs(currentX - x) >= abs(currentY - y)) {
    Serial.println("runX");
    Serial.println("currentX: " + String(currentX) + " x: " + String(x));
    Serial.println("currentY: " + String(currentY) + " y: " + String(y));
    runX(x);
  } else {
    Serial.println("runY");
    Serial.println("currentX: " + String(currentX) + " x: " + String(x));
    Serial.println("currentY: " + String(currentY) + " y: " + String(y));
    runY(y);
  }
}

void motor::runX(int x) {
  if (x == currentX) {
    completeX = true;
    return;
  } else completeX = false;

  targetX = x;

  if (targetX > currentX) dir = Forward;
  else dir = Backward;

  startX = currentX;

  tmr = millis();
  moveXLoopRunning = true;
  completeY = true;
}

void motor::runY(int y) {
  if (y == currentY) {
    completeY = true;
    return;
  } else completeY = false;

  targetY = y;
  isCorrectingY = false;
  compass->on();

  if (targetY > currentY) dir = Left;
  else dir = Right;

  startY = currentY;
  tmr = millis();
  // Serial.println("startY: " + String(startY) + " currentY: " + String(currentY) + " targetY: " + String(targetY));
  moveYLoopRunning = true;
  completeX = true;
}

void motor::setBlocked(bool isBlocked) {
  if (isBlocked) {
    pause = true;
    
  }
  else {
    if (pause) {
      startX = currentX;
      startY = currentY;

      tmr = millis();
    }
    pause = false;
  }
}

void motor::setCurrentPosition(int x, int y) {
  startX = x;
  startY = y;
  currentX = x;
  currentY = y;

  tmr = millis();
  Serial.println("SET POS " + String(x) + String(" ") + String(y));
}

void motor::setSpeed(int speed, Type type) {
  switch (type) {
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

void motor::setSpeed4(int sp1, int sp2, int sp3, int sp4) {
  setSpeed(sp1, BL);
  setSpeed(sp2, BR);
  setSpeed(sp3, FL);
  setSpeed(sp4, FR);
}

void motor::go(Move _move) {
  move = _move;
  switch (move) {
    case Forward:
      motor_run(FL, B);
      motor_run(FR, B);
      motor_run(BL, B);
      motor_run(BR, B);
      // setSpeed(150, ALL);
      break;

    case Backward:
      motor_run(FL, F);
      motor_run(FR, F);
      motor_run(BL, F);
      motor_run(BR, F);
      setSpeed(150, ALL);
      break;

    case Right:
      motor_run(FL, B);
      motor_run(FR, F);
      motor_run(BL, F);
      motor_run(BR, B);
      setSpeed(150, BL);
      setSpeed(150, BR);
      setSpeed(165, FL);
      setSpeed(165, FR);
      break;

    case Left:
      motor_run(FL, F);
      motor_run(FR, B);
      motor_run(BL, B);
      motor_run(BR, F);
      setSpeed(150, BL);
      setSpeed(150, BR);
      setSpeed(163, FL);
      setSpeed(163, FR);
      break;

    case RotateL:       //  Против часовой
      motor_run(FL, F);
      motor_run(FR, B);
      motor_run(BL, F);
      motor_run(BR, B);
      setSpeed(120, ALL);
      break;
    
    case RotateR:       //  По часовой
      motor_run(FL, B);
      motor_run(FR, F);
      motor_run(BL, B);
      motor_run(BR, F);
      setSpeed(120, ALL);
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
  switch (dir) {
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

  switch (motor) {
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

bool motor::isCompleted() {
  return completeX && completeY;
}

void motor::clearState() {
  completeX = false;
  completeY = false;
}