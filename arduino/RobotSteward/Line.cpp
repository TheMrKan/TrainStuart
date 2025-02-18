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

void Line:goLine(short dirF, short dirB = 0, bool only = false) {
    if (!only) {
        if (dirB == 0) {
            if (dirF > 0) {
                motors->go(Right);
            } else {
                motors->go(Left);
            }
        } else {
            if (dirF > 0) {
                motors->specialGo(Right, dirB > 0 ? Right : Left);
            } else {
                motors->specialGo(Left, dirB > 0 ? Right : Left);
            }
        }
    } else {
        if (dirF == 0) {
            motors->specialGo(Stop, dirB > 0 ? Right : Left);
        } else {
            motors->specialGo(dirF > 0 ? Right : Left, Stop);
        }
    }

    findState = state0;

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

/*
        |
    0 0 1 0 0
        |
        |
        |
    0 0 1 0 0
        |

        |
  0 0 0 1 0
        |
        |
        |
      0 1 0 0 0
        |

        |
0 0 0 0 1
        |
        |
        |
        1 0 0 0 0
        |

         |
0 0 0 0 0|
         |
         |
         |
       0 1 0 0 0
         |

         |
0 0 0 0 0|
         |
         |
         |
0 0 0 0 0|
         |
*/

// Функция проверки массива на монотонность (если все элементы одинаковые и равны state)
bool isUniform(bool array[5], bool state) {
    bool firstElem = array[0];

    if (firstElem != state) return false;
    for (int i = 1; i < 5; i++) {
        if (array[i] != firstElem)
            return false;
    }

    return true;
}

void Line::tickLine() {
  if (!LineLoop) return;
  
  checkStates();

  if (linesValF[2]) {
      motors->setSpeed4(-1, -1, 0, 0);
  }
  if (linesValB[2]) {
      motors->setSpeed4(0, 0, -1, -1);
  }

  if (linesValF[2] && linesValB[2]) {
    state = true;
    LineLoop = false;
    return;
  }
}

void Line::findLine(bool active) {
    FindLoop = active;
}

void Line::tickFind() {
    // Выполнять только когда стоим над линией!!!
    if (!FindLoop) return;

    checkStates();

    switch (findState) {
        case state0: // Пустое состояние - ничего не делать
            break;
        case state1: // Когда оба датчика стоят не на линии (по разные стороны)
            findTime = millis();
            bool flagWrongRot_R = false;
            // Пока датчики полностью не на линии
            while (!isUniform(linesValF, false) || !isUniform(linesValB, false)) {
                checkStates();
                motors->go(RotateR);
                if (millis() - findTime >= findDelay) {
                    flagWrongRot_R = true;
                    break;
                }
            }
            motors->go(Stop);
            if (flagWrongRot_R) {
                while (!isUniform(linesValF, false) || !isUniform(linesValB, false)) {
                    checkStates();
                    motors->go(RotateL);
                }
                motors->go(Stop);
            }

            // Переход к следующей обработке выравнивания
            checkStates();

            // Если оба датчика видят линию
            if (!isUniform(linesValF, false) && !isUniform(linesValB, false)) {
                int frontS = -1, backS = -1;
                for (int i = 0; i < 5; i++) {
                    if (linesValF[i]) frontS = i;
                    if (linesValB[i]) backS = i;
                }

                // Если один датчик стоит на линии (по центру)
                if (frontS == 2 || backS == 2) {
                    if (frontS == 2 && backS == 2) findState = state7;
                    else findState = state6;
                }
                // Если оба датчика по одну сторону от линии
                else if (frontS > 2 && backS > 2 || frontS < 2 && backS < 2) findState = state3;
                // Если датчики по разные стороны от линии
                else if (frontS > 2 && backS < 2 || frontS < 2 && backS > 2) findState = state4;
            }
            // Если только один датчик на линии, а второй нет
            else findState = state2;
        case state2: // Когда только один из датчиков стоит на линии, а другой - нет
        case state3: // Когда оба датчика видят линию, но оба не по центру (оба датчика по одну сторону от линии)
            checkStates();

            int frontS = -1;
            for (int i = 0; i < 5; i++) {
                if (linesValF[i]) frontS = i;
            }

            // Если линия справа от робота -> (едем влево) и наоборот
            if (frontS > 2) goLine(-1);
            else goLine(1);

            break;
        case state4: // Когда оба датчика видят линию, но оба не по центру (датчики по разные стороны от линии)
            checkStates();

            int frontS = -1;
            for (int i = 0; i < 5; i++) {
                if (linesValF[i]) frontS = i;
            }

            // Если линия относительно передних датчиков справа -> едем (передом влево, задом - вправо) и наоборот
            if (frontS > 2) goLine(-1, 1);
            else goLine(1, -1);

            break;
        case state5: // Когда один датчик стоит ровно (по центру), а второй не на линии
        case state6: // Когда один датчик стоит ровно (по центру), а второй просто на линии
            checkStates();

            // Поиск стороны, которая уже ровно на линии (по центру)
            if (linesValF[2]) {
                int b = -1;
                for (int i = 0; i < 5; i++) {
                    if (linesValB[i]) b = i;
                }

                // Если линия относительно задних справа -> едем (только задом влево) и наоборот
                if (b > 2) goLine(0, -1, true);
                else goLine(0, 1, true);

                break;
            } else {
                int f = -1;
                for (int i = 0; i < 5; i++) {
                    if (linesValF[i]) f = i;
                }

                // Если линия относительно передних справа -> едем (только передом влево) и наоборот
                if (f > 2) goLine(-1, 0, true);
                else goLine(1, 0, true);

                break;
            }
        case state7: // Когда оба датчика стоят ровно (по центру)
            motors->go(Stop);
            FindLoop = false; // Завершаем поиск
            findState = state0; // Сбрасываем состояние
            break;
    }
}

/*
void Line::tickFind() {
    // Выполнять только когда стоим над линией!!!
    if (!FindLoop) return;

    checkStates();

    switch (findState) {
        case state0: // Пустое состояние - ничего не делать
            break;

        case state1: // Когда оба датчика стоят не на линии (по разные стороны)
            if (!isUniform(linesValF, false) || !isUniform(linesValB, false)) {
                if (millis() - findTime >= findDelay) {
                    // Если время поиска истекло, меняем направление вращения
                    motors->go(RotateL);
                } else {
                    // Вращаемся вправо
                    motors->go(RotateR);
                }
            } else {
                // Оба датчика на линии, переходим к следующему состоянию
                motors->go(Stop);
                findState = state2;
            }
            break;

        case state2: // Когда только один из датчиков стоит на линии, а другой - нет
            if (linesValF[2] || linesValB[2]) {
                // Если один из средних датчиков на линии, переходим к следующему состоянию
                findState = state3;
            } else {
                // Продолжаем поиск
                motors->go(RotateR);
            }
            break;

        case state3: // Когда оба датчика видят линию, но оба не по центру (оба датчика по одну сторону от линии)
            if (linesValF[2] && linesValB[2]) {
                // Оба средних датчика на линии, завершаем поиск
                motors->go(Stop);
                findState = state7;
            } else {
                // Корректируем движение
                if (linesValF[2]) {
                    // Передний средний датчик на линии, корректируем заднюю часть
                    motors->setSpeed4(0, 0, 100, 100); // Задние моторы активны
                } else if (linesValB[2]) {
                    // Задний средний датчик на линии, корректируем переднюю часть
                    motors->setSpeed4(100, 100, 0, 0); // Передние моторы активны
                }
            }
            break;

        case state4: // Когда оба датчика видят линию, но оба не по центру (датчики по разные стороны от линии)
            if (linesValF[2] && linesValB[2]) {
                // Оба средних датчика на линии, завершаем поиск
                motors->go(Stop);
                findState = state7;
            } else {
                // Корректируем движение
                if (linesValF[2]) {
                    // Передний средний датчик на линии, корректируем заднюю часть
                    motors->setSpeed4(0, 0, 100, 100); // Задние моторы активны
                } else if (linesValB[2]) {
                    // Задний средний датчик на линии, корректируем переднюю часть
                    motors->setSpeed4(100, 100, 0, 0); // Передние моторы активны
                }
            }
            break;

        case state5: // Когда один датчик стоит ровно (по центру), а второй не на линии
        case state6: // Когда один датчик стоит ровно (по центру), а второй просто на линии
            if (linesValF[2] && linesValB[2]) {
                // Оба средних датчика на линии, завершаем поиск
                motors->go(Stop);
                findState = state7;
            } else {
                // Корректируем движение
                if (linesValF[2]) {
                    // Передний средний датчик на линии, корректируем заднюю часть
                    motors->setSpeed4(0, 0, 100, 100); // Задние моторы активны
                } else if (linesValB[2]) {
                    // Задний средний датчик на линии, корректируем переднюю часть
                    motors->setSpeed4(100, 100, 0, 0); // Передние моторы активны
                }
            }
            break;

        case state7: // Когда оба датчика стоят ровно (по центру)
            motors->go(Stop);
            FindLoop = false; // Завершаем поиск
            findState = state0; // Сбрасываем состояние
            break;
    }
}
*/

void Line:tickLiteral() {
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
