#include "Containers.h"
#include <Arduino.h>

#include <Multiservo.h>

#include "defs.h"

Containers::Containers(Multiservo* _servo, Box _box) {
    servo = _servo;
    box = _box;
    // pin = _pin;
    if (box == UP_BACK) {
        right = UpBack::Right;
        left = UpBack::Left;
        center = UpBack::Center;
    } else if (box == UP_FRONT) {
        right = UpFront::Right;
        left = UpFront::Left;
        center = UpFront::Center;
    } else if (box == DOWN) {
        right = Down::Right;
        left = Down::Left;
        center = Down::Center;
    }
}
// Containers::Containers(Multiservo* _servo, Box _box, int _pin) : servo(_servo), box(_box), pin(_pin) {}

void Containers::begin() {
    servo->write(center);
}

void Containers::set_position(BoxState _state) {
    BoxState new_state = _state;

    switch (new_state) {
        case CLOSE:
            if (state == OPEN_RIGHT) rotate(right, center);
            else rotate(left, center);
            break;
        case OPEN_LEFT:
            rotate(center, left);
            break;
        case OPEN_RIGHT:
            rotate(center, right);
            break;
    }
    state = new_state;
}

void Containers::rotate(int start, int end) {
    current_angle = start;
    target_angle = end;
    tmr = millis();
    tickLoopRunning = true;
}

void Containers::tick() {
    if (!tickLoopRunning) return;

    if (current_angle == target_angle) {
        tickLoopRunning = false;
        return;
    }

    if (millis() - tmr > 50) {
        tmr = millis();
        int delta = current_angle - target_angle;
        int absStep;

        if (abs(delta) > 10) absStep = 5;
        else if (abs(delta) > 5) absStep = 2;
        else absStep = 1;

        if (delta > 0) current_angle -= absStep;
        else current_angle += absStep;

        servo->write(current_angle);
    }

}