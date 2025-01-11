#ifndef ROBOTSTEWARD_RotationPID
#define ROBOTSTEWARD_RotationPID

namespace PID {
  enum MovePID {
    F = 0, B, R, L
  };

  enum StatusPID {
    FATAL_ERROR = 0,
    FAIL,
    MEAN_FAIL,
    HIGH_FAIL,
    // POSITIVE_HIGH_FAIL,
    // POSITIVE_MEAN_FAIL,
    // POSITIVE_FAIL,
    // NEGATIVE_HIGH_FAIL,
    // NEGATIVE_MEAN_FAIL,
    // NEGATIVE_FAIL,
    OK
  };

  struct StatePID {
    bool isRotate;
    bool dir;
    int delta;
    int intensity;
    StatusPID st;
  };
};



class RotationPID {
public:
  RotationPID() {}
  void setConfig(float _normalAngle, int _speed, PID::MovePID _move) {
    normalAngle = _normalAngle;
    speed = _speed;
    move = _move;
  }
  void setAngle(float _angle) {
    angle = _angle;
  }

  
  
  void rotate() {}
  void setSpeed() {
    struct PID::StatePID currentState = off_course(normalAngle, angle);
    // Serial.println(currentState.isRotate);
    if (currentState.isRotate) return;
    // if (currentState.st == PID::FATAL_ERROR) {
    //   Serial.println("FATAL_ERROR");
    //   FR = 0;
    //   FL = 0;
    //   BR = 0;
    //   BL = 0;
    //   rotate();
    //   return;
    // }
    if (!currentState.isRotate) {
      if (move == PID::F || move == PID::B) {
        Serial.println("GO F B");
        FR = 150;
        FL = 150;
        BR = 150;
        BL = 150;
      } else if (move == PID::R || move == PID::L){
        Serial.println("GO R L");
        /*
        setSpeed(150, BL);
        setSpeed(150, BR);
        setSpeed(162, FL);
        setSpeed(162, FR);
        */
        FR = 162;
        FL = 162;
        BR = 150;
        BL = 150;
      }
    }
    if (currentState.isRotate) { // Сбились с курса
      int step;
      if (currentState.st == PID::FAIL) step = 1;
      if (currentState.st == PID::MEAN_FAIL) step = 3;
      if (currentState.st == PID::HIGH_FAIL) step = 5;

      if (currentState.dir) { // Направление положительное
        if (move == PID::R) {
          FR = speed - step;
          FL = speed - step;
          BR = speed + step;
          BL = speed + step;
        } else if (move == PID::L) {
          FR = speed + step;
          FL = speed + step;
          BR = speed - step;
          BL = speed - step;
        }
      } else {
        if (move == PID::L) {
          FR = speed - step;
          FL = speed - step;
          BR = speed + step;
          BL = speed + step;
        } else if (move == PID::R) {
          FR = speed + step;
          FL = speed + step;
          BR = speed - step;
          BL = speed - step;
        }
      }
    }

    Serial.println("FR: " + String(FR) + " FL: " + String(FL) + " BR: " + String(BR) + " BL: " + String(BL) + " Angle: " + String(angle) + " Delta: " + String(currentState.delta));
  }
  int FR = speed, FL = speed, BR = speed, BL = speed;
private:
  PID::MovePID move;
  PID::StatusPID status;
  float angle, normalAngle;
  int speed;
  
  // Filter
  float _err_measure = 0.8;  // примерный шум измерений
  float _q = 0.1;   // скорость изменения значений 0.001-1, варьировать самому
  

  float simpleKalman(float newVal) {
    float _kalman_gain, _current_estimate;
    static float _err_estimate = _err_measure;
    static float _last_estimate;

    _kalman_gain = (float)_err_estimate / (_err_estimate + _err_measure);
    _current_estimate = _last_estimate + (float)_kalman_gain * (newVal - _last_estimate);
    _err_estimate =  (1.0 - _kalman_gain) * _err_estimate + fabs(_last_estimate - _current_estimate) * _q;
    _last_estimate = _current_estimate;
    return _current_estimate;
  }

  struct PID::StatePID off_course(float normal, float current) {
    struct PID::StatePID result;
    float absDelta = abs(normal - current);
    // Serial.println(absDelta);
    if (absDelta > 20) {
      // Serial.println("FATAL_ERROR ------------ SET");
      result.st = PID::FATAL_ERROR;
    }

    if (absDelta < 1.5) result.isRotate = false;
    else {
      result.isRotate = true;
      if (normal - current > 0) {
        result.delta = normal - current;
        result.dir = true;
        if (result.delta > 2) result.st = PID::FAIL;
        if (2 <= result.delta && result.delta < 5) result.st = PID::MEAN_FAIL;
        else result.st = PID::HIGH_FAIL;
      } else if (normal - current < 0) {
        result.delta = abs(normal - current);
        result.dir = false;
        if (result.delta > 2) result.st = PID::FAIL;
        if (2 <= result.delta && result.delta < 5) result.st = PID::MEAN_FAIL;
        else result.st = PID::HIGH_FAIL;
      }
    }

    return result;
  }
};

#endif