#include "Line.h"
#include <Arduino.h>
#include "motor.h"

Line::Line() {
  linesF[0] = LineF::far_left;
  linesF[1] = LineF::left;
  linesF[2] = LineF::center;
  linesF[3] = LineF::right;
  linesF[4] = LineF::far_right;

  linesB[0] = LineB::far_left;
  linesB[1] = LineB::left;
  linesB[2] = LineB::center;
  linesB[3] = LineB::right;
  linesB[4] = LineB::far_right;
}

void Line::init() {
  for (int i = 0; i < 5; i++) {
    pinMode(lines[i], INPUT);
  }
}

void Line::checkStates() {
  for (int i = 0; i < 5: i++) {
    linesValF[i] = digitalRead(linesF[i]);
    linesValB[i] = digitalRead(linesB[i]);
  }
}

void Line:goLine(short dir) {
  if (dir > 0) {
    motors->go(Right);
  } else {
    motors->go(Left);
  }

  LineLoop = true;
}

void Line::LinearMove(bool active) {
  LinearLoop = active;
}

void Line::LiteralMove(short dir, bool active) {
  LiteralLoop = active;
}

void Line::tick() {
  tickLine();
  tickLiteral();
  tickLinear();
}

void Line::tickLine() {
  if (!LineLoop) return;
  
  checkStates();

  if (linesF[2]) motors->setSpeed4(-1, -1, 0, 0);
  if (linesB[2]) motors->setSpeed4(0, 0, -1, -1);

  if (linesF[2] && lineB[2]) {
    state = true;
    LineLoop = false;
    return;
  }
}

void Line:tickLiteral() {
  if (!LiteralLoop) return;
  
  checkStates();
}

void Line::tickLinear() {
  if (!LinearLoop) return;

  checkStates();
}

void Line::print() {
  for (int i = 0; i < 5; i++) {
    Serial.print(String(digitalRead(linesF[i])) + " ");
  }
  Serial.println();
  for (int i = 0; i < 5; i++) {
    Serial.print(String(digitalRead(linesB[i])) + " ");
  }
  Serial.println();
}

bool Line::isCompleted() {
  if (state) {
    state = false;
    return true;
  }
  return false;
}
