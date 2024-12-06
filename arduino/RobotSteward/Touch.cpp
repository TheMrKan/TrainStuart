#include "Arduino.h"
#include "Touch.h"

Touch::Touch(int _pin) {
  pin = _pin;
  state = WAITING;
}

void Touch::tick() {
  detector.tick(digitalRead(pin) == 1);
  state = detector.state;

  switch (detector.state) {
    case FOUND:
    case LOST:
      struct Message outgoingMessage = IO.produceMessage(COMMAND, "Tch", detector.state == FOUND ? 1 : 0);
      IO.sendMessage(outgoingMessage);
      break;
  }
}

bool Touch::isTouched() {
  return state == FOUND || state == TRACKING;
}