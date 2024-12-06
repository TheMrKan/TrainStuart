#ifndef ADUINO_MOTOR_H
#define ADUINO_MOTOR_H

#include "Laser.h"

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
  Rotate
};

class motor {
public:
  motor(Laser* _laserF, Laser* _laserB);
  // motor();
  void begin();
  void tick();
  void setSpeed(int speed, Type type);
  void run(int x, int y);
  void go(Move _move);
  bool isCompleted();

  void clearState();
  void setCurrentPosition(int x, int y);
  void setBlocked(bool isBlocked);
private:
  Laser *laserF, *laserB;
  Move move, dir;
  void motor_run(Type motor, Direction dir);

  void tickX();
  void tickY();

  void runX(int x);
  void runY(int y);

  bool moveXLoopRunning = false, moveYLoopRunning = false, pause = false;
  unsigned long tmr;
  unsigned long targetTime;

  int currentX = 0, currentY = 0;
  int targetX, targetY;
  int startX, startY;

  bool completeX = false, completeY = false;

  float SPEED_X = (float)215 / 12;
  // делим на коэффиценты для корректировки. Если должен был проехать 75, а проехал 50 - коэффицент 1.5
  float SPEED_Y_RIGHT = (float)44 / 5 / 0.9375;
  float SPEED_Y_LEFT = (float)82 / 5 / 1.55;
};

#endif //ADUINO_MOTOR_H