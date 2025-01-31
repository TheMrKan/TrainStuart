#ifndef ROBOTSTEWARD_RotationPID
#define ROBOTSTEWARD_RotationPID

namespace PID {
    enum Move {
        F, B, R, L
    };

    enum Status {
        FATAL_ERROR,
        FAIL,
        MEAN_FAIL,
        HIGH_FAIL,
        OK
    };

    struct State {
        bool dir;
        PID::Status st;
    };
}


class RotationPID {
public:
    RotationPID() {}
    void setConfig(float _normalAngle, int _speed, PID::Move _move) {
        // normalAngle = _normalAngle;
        speed = _speed;
        move = _move;
    }

    void setMove(PID::Move _move) {
        move = _move;
    }
    void setDelta(int _delta) {
        delta = _delta;
    }
    void PrintData() {
    }

    void setSpeed() {
      struct PID::State currentState = readState();
      if (currentState.st == PID::FATAL_ERROR) {
        FR = 0;
        FL = 0;
        BR = 0;
        BL = 0;
        return;
      }

      int step;
      if (currentState.st == PID::OK) step = 0;
      if (currentState.st == PID::FAIL) step = 5;
      if (currentState.st == PID::MEAN_FAIL) step = 10;
      if (currentState.st == PID::HIGH_FAIL) step = 15;


      if (currentState.dir) { // Направление положительное
        if (move == PID::F || move == PID::B) {
          FR = speed + step;
          FL = speed - step;
          BR = speed + step;
          BL = speed - step;
        } else {
          FR = speed - step;
          FL = speed - step;
          BR = speed + step;
          BL = speed + step;
        }
      } else {
        if (move == PID::F || move == PID::B) {
          FR = speed - step;
          FL = speed + step;
          BR = speed - step;
          BL = speed + step;
        } else {
          FR = speed + step;
          FL = speed + step;
          BR = speed - step;
          BL = speed - step;
        }
      }

      Serial.println(
          "FR: " + String(FR) +
          " FL: " + String(FL) +
          " BR: " + String(BR) +
          " BL: " + String(BL) +
          " DELTA: " + String(delta) +
          " STATE: " + String(currentState.st) +
          " DIR: " + String(currentState.dir));

    }

    // void setSpeed() {
    //     struct PID::State currentState = off_course(normalAngle, angle);
    //     // Serial.println(currentState.delta);
    //     if (!currentState.isRotate) return;
    //     if (currentState.st == PID::FATAL_ERROR) {
    //         FR = 0;
    //         FL = 0;
    //         BR = 0;
    //         BL = 0;
    //         rotate();
    //         return;
    //     }

    //     if (currentState.isRotate) { // Сбились с курса
    //         int step;
            // if (currentState.st == PID::FAIL) step = 1;
            // if (currentState.st == PID::MEAN_FAIL) step = 3;
            // if (currentState.st == PID::HIGH_FAIL) step = 5;

            // if (currentState.dir) { // Направление положительное
            //     if (move == PID::F || move == PID::B) {
            //         FR = speed - step;
            //         FL = speed - step;
            //         BR = speed + step;
            //         BL = speed + step;
            //     }
            // } else {
            //     FR = speed + step;
            //     FL = speed + step;
            //     BR = speed - step;
            //     BL = speed - step;
            // }
    //     }

        // Serial.println(
        //         "FR: " + String(FR) +
        //         " FL: " + String(FL) +
        //         " BR: " + String(BR) +
        //         " BL: " + String(BL) +
        //         " Angle: " + String(angle) +
        //         " Delta: " + String(currentState.delta));
    // }
    int FR, FL, BR, BL;
private:
    PID::Move move;
    PID::Status status;
    int speed, delta;

    struct PID::State readState() {
      struct PID::State result;

      result.dir = delta > 0;

      int absDelta = abs(delta);
      if (absDelta > 10) {
        result.st = PID::FATAL_ERROR;
      }
      else if (absDelta > 5) {
        result.st = PID::HIGH_FAIL;
      }
      else if (absDelta > 2) {
        result.st = PID::MEAN_FAIL;
      }
      else {
        result.st = PID::OK;
      }

      return result;
    }

    // struct PID::State off_course(float normal, float current) {
    //     struct PID::State result;
    //     float absDelta = abs(normal - current);
    //     // Serial.println(absDelta);
    //     if (absDelta > 10) {
    //         result.st = PID::FATAL_ERROR;
    //     }

    //     if (absDelta < 0.8) result.isRotate = false;
    //     else {
    //         result.isRotate = true;
    //         if (normal - current > 0) {
    //             result.delta = normal - current;
    //             result.dir = true;
                // if (result.delta > 2) result.st = PID::FAIL;
                // if (2 <= result.delta && result.delta < 5) result.st = PID::MEAN_FAIL;
                // else result.st = PID::HIGH_FAIL;
    //         } else if (normal - current < 0) {
    //             result.delta = abs(normal - current);
    //             result.dir = false;
    //             if (result.delta > 2) result.st = PID::FAIL;
    //             if (2 <= result.delta && result.delta < 5) result.st = PID::MEAN_FAIL;
    //             else result.st = PID::HIGH_FAIL;
    //         }
    //     }

    //     return result;
    // }
};

#endif