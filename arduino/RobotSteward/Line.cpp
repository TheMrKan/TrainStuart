#include "Line.h"
#include <Arduino.h>
#include "motor.h"
#include "defs.h"

Line::Line() {
  linesF[0] = LineF::far_left;
  linesF[1] = LineF::left;
  linesF[2] = LineF::center;
  linesF[3] = LineF::right;
  linesF[4] = LineF::far_right;

  linesB[0] = LineB::far_right;
  linesB[1] = LineB::right;
  linesB[2] = LineB::center;
  linesB[3] = LineB::left;
  linesB[4] = LineB::far_left;
}

void Line::init() {
  for (int i = 0; i < 5; i++) {
    pinMode(linesF[i], INPUT);
    pinMode(linesB[i], INPUT);
  }
}

void Line::checkStates() {
  for (int i = 0; i < 5; i++) {
    // ! -> на откражение (лента максимально светлая)
    linesValF[i] = digitalRead(linesF[i]);
    linesValB[i] = digitalRead(linesB[i]);
  }
}

void Line::goLine(short dir) {
  if (dir > 0) {
    motors->go(Right);
  } else {
    motors->go(Left);
  }

  LineLoop = true;
  statusF = Default;
  statusB = Default;
  statusFGuess = Default;
  statusBGuess = Default;
  statusFGuessTime = 0;
  statusBGuessTime = 0;
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
//  checkStates();
  if (!LineLoop) return;
  
  calcStatusFilter();
  Serial.println(String(statusF) + " " + String(statusB));
  
  if (statusF == OK) {
    motors->setSpeed4(-1, -1, 0, 0);
  }
  if (statusB == OK) {
    motors->setSpeed4(0, 0, -1, -1);
  }

  if (statusF == OK && statusB == OK) {
    Serial.println("F and B stop");
    state = true;
    LineLoop = false;
    motors->go(Stop);
    return;
  }

  if (statusF == LEFT) {
    motors->specialGo(Right, F);
  } else if (statusF == RIGHT) {
    motors->specialGo(Left, F);
  } 

  if (statusB == LEFT) {
    motors->specialGo(Right, B);
  } else if (statusB == RIGHT) {
    motors->specialGo(Left, B);
  } 

  if (linesValF[2] && linesValB[2]) {
    state = true;
    LineLoop = false;
    motors->go(Stop);
    return;
  }
}

void Line::calcStatusFilter() {
  struct LineStatus calc = calcStatus();

  if (calc.forward != statusFGuess) {
    statusFGuess = calc.forward;
    statusFGuessTime = millis();
  }

  if (statusFGuess != statusF && millis() - statusFGuessTime > 50) {
    statusF = statusFGuess;
  }

  if (calc.backward != statusBGuess) {
    statusBGuess = calc.backward;
    statusBGuessTime = millis();
  }

  if (statusBGuess != statusB && millis() - statusBGuessTime > 50) {
    statusB = statusBGuess;
  }
}

struct LineStatus Line::calcStatus() {
  checkStates();
  struct LineStatus result;
  result.forward = statusF;
  result.backward = statusB;
  
 if (linesValF[0] || linesValF[1]) result.forward = LEFT;
 else if (linesValF[3] || linesValF[4]) result.forward = RIGHT;
 else if (linesValF[2]) result.forward = OK;

 if (linesValB[0] || linesValB[1]) result.backward = LEFT;
 else if (linesValB[3] || linesValB[4]) result.backward = RIGHT;
 else if (linesValB[2]) result.backward = OK;

 return result;
}

void Line::findLine(bool active) {
    FindLoop = false;
    findState = state1;
}

void Line::tickLiteral() {
  if (!LiteralLoop) return;
  
  checkStates();
}

void Line::tickLinear() {
    if (!LinearLoop) return;

    checkStates();

    // Определяем, насколько робот отклоняется от линии
    int errorF = 0; // Ошибка для передних датчиков
    int errorB = 0; // Ошибка для задних датчиков

    // Рассчитываем ошибку для передних датчиков
    for (int i = 0; i < 5; i++) {
        if (linesValF[i]) {
            errorF += (i - 2); // Средний датчик (i=2) дает ошибку 0
        }
    }

    // Рассчитываем ошибку для задних датчиков
    for (int i = 0; i < 5; i++) {
        if (linesValB[i]) {
            errorB += (i - 2); // Средний датчик (i=2) дает ошибку 0
        }
    }

    // Усредняем ошибку
    int error = (errorF + errorB) / 2;

    // Корректируем движение робота
    if (error > 0) {
        // Робот отклоняется вправо, корректируем влево
        motors->setSpeed4(100, 100, 80, 80); // Левые моторы медленнее
    } else if (error < 0) {
        // Робот отклоняется влево, корректируем вправо
        motors->setSpeed4(80, 80, 100, 100); // Правые моторы медленнее
    } else {
        // Робот едет ровно
        motors->setSpeed4(100, 100, 100, 100); // Все моторы на одной скорости
    }
}

bool Line::isCompleted() {
  if (state) {
    state = false;
    return true;
  }
  return false;
}
