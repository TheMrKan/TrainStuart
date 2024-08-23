//
// Created by Nikit on 22.08.2024.
//

#ifndef ADUINO_HEAD_H
#define ADUINO_HEAD_H
#include <Arduino.h>

#include <Multiservo.h>
#include "defs.h"


class Head {
public:
    Head(Multiservo* _servo);
    void begin();
    void home();
    void tick();

    void rotate(int x, int y);
    void rotateX(int x);
    void rotateY(int y);
    void stop();

    bool getState();
private:
    void tickX();
    void tickY();
    Multiservo* servo;
    bool headLoopRunning = false, servoLoopRunning = false;
    bool stateX = false;

    unsigned long lowTimer;

    bool endFlag = false, dir, awaitFlag = false;
    bool deltaSign = false;

    int targetTickX = 0, targetY = 0; // Будущее положение
    int currentX = 0, currentY = 0;   // Текущие углы
    const float angleTicks = MAX_TICK / (float)(headInputRight + abs(headInputLeft));
    int countY = 0;

    byte power = 255;

    void zero();
    bool isEnd() {
        return !digitalRead(END_CAP);
    }

    static void isr();
};


#endif //ADUINO_HEAD_H
