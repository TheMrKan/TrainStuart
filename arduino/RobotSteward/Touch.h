#ifndef TOUCH_H
#define TOUCH_H

#include "SerialIO.h"
#include "ContinuousDetector.h"

extern SerialIO IO;

class Touch {
  public:
    Touch(int _pin);
    void tick();
    bool isTouched();
    DetectorState state;
    int pin;
  private:
    const int FIND_DELAY = 50;
    const int LOSE_DELAY = 1000;
    ContinuousDetector detector = ContinuousDetector(FIND_DELAY, LOSE_DELAY);
};
#endif