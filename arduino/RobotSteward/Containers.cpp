#include "Containers.h"
#include <Arduino.h>

#include <Multiservo.h>

#include "defs.h"

Containers::Containers(Multiservo* _servo, Box _box) {
    servo = _servo;
    box = _box;
    pin = -1;
    
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

Containers::Containers(Multiservo* _servo, Box _box, int _pin) {
  servo = _servo;
  box = _box;
  pin = _pin;
}

void Containers::begin() {
    if (pin == -1) servo->write(center);
    
    if (pin != -1) {
      pinMode(pin, INPUT);
      while (!digitalRead(pin)) {
        Serial.println("------------------------------------ Drawer open !!!!! ------------------------------------");
        servo->write(Drawer::RightSlow);
      }
      servo->write(Drawer::Stop);
    }
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

void Containers::togleTablet(BoxState _state) {
  BoxState new_state = _state;
  tmr = millis();
  stateC = false;
  tickDrawerLoop = true;

  switch(new_state) {
    case CLOSE:
      if (state == OPEN_RIGHT) drawerCurrentAngle = Drawer::Left;
      if (state == OPEN_LEFT) drawerCurrentAngle = Drawer::Right;
      break;
    case OPEN_RIGHT:
      drawerCurrentAngle = Drawer::Right;
      break;
    case OPEN_LEFT:
      drawerCurrentAngle = Drawer::Left;
      break;
  }
  lastState = state;
  state = new_state;
}

void Containers::rotate(int start, int end) {
    current_angle = start;
    target_angle = end;
    tmr = millis();
    stateC = false;
    tickLoopRunning = true;
}

void Containers::tick() {
  tickBox();
  tickDrawer();
}

void Containers::tickBox() {
    if (!tickLoopRunning) return;

    if (current_angle == target_angle) {
        tickLoopRunning = false;
        stateC = true;
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
    stateC = false;
}

void Containers::tickDrawer() {
  if (!tickDrawerLoop) return;

  if (lastState == OPEN_RIGHT || lastState == OPEN_LEFT) {
    Serial.println("Drawer CLOSED");
    if (!digitalRead(pin)) servo->write(drawerCurrentAngle);
    else {
      servo->write(Drawer::Stop);
      stateC = true;
      tickDrawerLoop = false;
      return;
    }
  } else {
    Serial.println("Drawer OPENED");
    if (millis() - tmr < 3000) servo->write(drawerCurrentAngle);
    else {
      servo->write(Drawer::Stop);
      stateC = true;
      tickDrawerLoop = false;
      return;
    }
  }
}

bool Containers::isCompleted() {
  if (stateC) {
    stateC = false;
    return true;
  }
  return false;
}
