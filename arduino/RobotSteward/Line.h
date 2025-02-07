#ifndef ADUINO_LINE_H
#define ADUINO_LINE_H
#include <Arduino.h>

class Line {
public:
  Line();

  void init();
  void tick();

  void print();
  void checkStates();

  void correcting();
  bool isCompleted();

  void goLine(short dir, bool active);
  void LinearMove();
  void LiteralMove(short dir, bool active);

  motor* motors;
  bool state = false;
private:
  int linesF[5];
  int linesB[5];
  
  bool linesValF[5] = {false, false, false, false, false};
  bool linesValB[5] = {false, false, false, false, false};

  bool LineLoop = false; // tickLine()
  bool LiteralLoop = false; // tickLiteral()
  bool LinearLoop = false; // tickLinear()

  void tickLine();
  void tickLiteral();
  void tickLinear();
};

#endif
