#include "ContinuousDetector.h"
#include <Arduino.h>

ContinuousDetector::ContinuousDetector(int _findDelay = 500, int _loseDelay = 500) {
  findDelay = _findDelay;
  loseDelay = _loseDelay;
  reset();
}

void ContinuousDetector::reset() {
  found = 0;
  lost = 0;
  isTracking = false;
  state = WAITING;
}

DetectorState ContinuousDetector::tick(bool value) {
  state = tickInternal(value);
  return state;
}

DetectorState ContinuousDetector::tickInternal(bool value) {
  if (!value) {
    if (found > 0 && !isTracking) {
      found = 0;
      return WAITING;    // FOUND_GUESS_FAILED
    }

    if (lost > 0) {
      if (millis() - lost > loseDelay) {
        reset();
        return LOST;
      }
      return TRACKING;    // LOST_GUESS_WAITING
    }

    if (found > 0) {
      lost = millis();
      return TRACKING;    // LOST_GUESS
    }
    return WAITING;
  }

  lost = 0;
  if (found == 0) {
    found = millis();
    return WAITING;    // FOUND_GUESS
  }

  if (!isTracking) {
    if (millis() - found > findDelay) {
      isTracking = true;
      return FOUND;
    }
    return WAITING;    // FOUND_GUESS_WAITING
  }

  return TRACKING;
}