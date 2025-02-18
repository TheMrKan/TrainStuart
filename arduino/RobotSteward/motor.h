#ifndef ADUINO_MOTOR_H
#define ADUINO_MOTOR_H

#include "Laser.h"
#include "CompassRemote.h"

enum Type {
  FL,
  FR,
  BL,
  BR,
  ALL
};

enum Direction {
  F,
  B,
  S
};

enum Move {
  Forward,
  Backward,
  Right,
  Left,
  Stop,
  RotateL,
  RotateR
};

class motor {
public:
  motor(Laser* _laserF, Laser* _laserB, CompassRemote* _compass);
  // motor();
  void begin();
  void tick();
  void setSpeed(int speed, Type type);
  void setSpeed4(int sp1, int sp2, int sp3, int sp4);
  void run(int x, int y);
  void go(Move _move);
  void specialGo(Move _spMove, Direction _d);
  bool isCompleted();

  void clearState();
  void setCurrentPosition(int x, int y);
  void setSpeedCorrection(int correction);
  void setBlocked(bool isBlocked);

  int currentX = 0, currentY = 0;
private:
  Laser *laserF, *laserB;
  CompassRemote *compass;
  Move move, dir;
  struct CompassData compassData;
  void motor_run(Type motor, Direction dir);

  void tickX();
  void tickY();
  void tickCorrectingY();

  void runX(int x);
  void runY(int y);

  bool moveXLoopRunning = false, moveYLoopRunning = false, pause = false;
  bool isCorrectingY = false;
  int speedCorrection = 0; // >0 - направо, <0 - налево
  unsigned long tmr;
  unsigned long targetTime;

  int targetX, targetY;
  int startX, startY;

  bool completeX = false, completeY = false;

  float SPEED_X = (float)215 / 12;
  // умножаем на коэффиценты для корректировки. Если должен был проехать 100, а проехал 114 - коэффицент 1.14
  float SPEED_Y_RIGHT = (float)55.5 / 5 * 1.12;
  float SPEED_Y_LEFT = (float)55.5 / 5 * 1.14;
};

#endif //ADUINO_MOTOR_H
