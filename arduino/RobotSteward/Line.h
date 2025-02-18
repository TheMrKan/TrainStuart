#ifndef ADUINO_LINE_H
#define ADUINO_LINE_H
#include <Arduino.h>

enum FindState {
    state0, // Пустое состояние - ничего не делать
    state1, // Когда оба датчика стоят не на линии (по разные стороны)
    state2, // Когда только один из датчиков стоит на линии, а другой - нет
    state3, // Когда оба датчика видят линию, но оба не по центру (оба датчика по одну сторону от линии)
    state4, // Когда оба датчика видят линию, но оба не по центру (датчики по разные стороны от линии)
    state5, // Когда один датчик стоит ровно (по центру), а второй не на линии
    state6, // Когда один датчик стоит ровно (по центру), а второй просто на линии
    state7  // Когда оба датчика стоят ровно (по центру)
};

class Line {
public:
  Line();

  void init();
  void tick();

  void checkStates();

  void correcting();
  bool isCompleted();

  void goLine(short dirF, short dirB = 0, bool only = false);
  void LinearMove(bool active);
  void LiteralMove(short dir, bool active);

  void findLine(bool active);

  motor* motors;
  bool state = false;
private:
  int linesF[5];
  int linesB[5];
  
  bool linesValF[5] = {false, false, false, false, false};
  bool linesValB[5] = {false, false, false, false, false};

  bool LineLoop = false;    // tickLine()
  bool LiteralLoop = false; // tickLiteral()
  bool LinearLoop = false;  // tickLinear()
  bool FindLoop = false;    // tickFind()

  FindState findState = state0; // Состояние поиска линии
  unsigned long findTime = 0;   // Таймер для поиска линии
  int findDelay = 2000;         // Время для поиска линии

  void tickLine();
  void tickLiteral();
  void tickLinear();
  void tickFind();
};

#endif
