#ifndef ROBOTSTEWARD_CONTAINERS_H
#define ROBOTSTEWARD_CONTAINERS_H
#include <Arduino.h>

#include <Multiservo.h>
#include "defs.h"


enum BoxState {
    CLOSE = 0,
    OPEN_LEFT = 1,
    OPEN_RIGHT = 2
};

enum Box {
    DRAWER_BACK = 5,    // Задний
    DRAWER_FRONT = 6,   // Передний
    UP_BACK = 3,        // Задний
    UP_FRONT = 2,       // Передний
    DOWN = 4            // Нижний
};

class Containers {
public:
    Containers(Multiservo* _servo, Box _box);
    Containers(Multiservo* _servo, Box _box, int _pin);

    void begin();
    void tick();
    void set_position(BoxState _state);
    void togleTablet(BoxState _state);   
    bool isCompleted();

    BoxState state;
private:
    Multiservo* servo;
    void rotate(int start, int end);
    void tickBox();
    void tickDrawer();
    Box box;
    BoxState lastState;
    int pin;

    bool tickLoopRunning = false, tickDrawerLoop = false, stateC = false;
    int right, left, center;

    int drawerCurrentAngle;

    int current_angle, target_angle;
    unsigned long tmr = 0;
};


#endif //ROBOTSTEWARD_CONTAINERS_H
