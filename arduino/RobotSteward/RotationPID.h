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
        bool isRotate;
        bool dir;
        int delta;
        int intensity;
        PID::Status st;
    };
}


class RotationPID {
public:
    RotationPID() {}

    void setConfig(float _normalAngle, int _speed, PID::Move _move) {
        normalAngle = _normalAngle;
        speed = _speed;
        move = _move;
    }
    void setNormalAngle(float _normalAngle) {
        normalAngle = _normalAngle;
    }
    void setMove(PID::Move _move) {
        move = _move;
    }
    void setAngle(float _angle) {
        angle = _angle;
    }
    void PrintData() {
    }


    void rotate() {}

    void setSpeed() {
        struct PID::State currentState = off_course(normalAngle, angle);
        // Serial.println(currentState.delta);
        if (!currentState.isRotate) return;
        if (currentState.st == PID::FATAL_ERROR) {
            FR = 0;
            FL = 0;
            BR = 0;
            BL = 0;
            rotate();
            return;
        }

        if (currentState.isRotate) { // Сбились с курса
            int step;
            if (currentState.st == PID::FAIL) step = 1;
            if (currentState.st == PID::MEAN_FAIL) step = 3;
            if (currentState.st == PID::HIGH_FAIL) step = 5;

            if (currentState.dir) { // Направление положительное
                if (move == PID::F || move == PID::B) {
                    FR = speed - step;
                    FL = speed - step;
                    BR = speed + step;
                    BL = speed + step;
                }
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
                " Angle: " + String(angle) +
                " Delta: " + String(currentState.delta));
    }
    int FR, FL, BR, BL;
private:
    PID::Move move;
    PID::Status status;
    float angle, normalAngle;
    int speed;

    // Filter
    float _err_measure = 0.8;  // примерный шум измерений
    float _q = 0.1;   // скорость изменения значений 0.001-1, варьировать самому


    float simpleKalman(float newVal) {
        float _kalman_gain, _current_estimate;
        static float _err_estimate = _err_measure;
        static float _last_estimate;

        _kalman_gain = (float) _err_estimate / (_err_estimate + _err_measure);
        _current_estimate = _last_estimate + (float) _kalman_gain * (newVal - _last_estimate);
        _err_estimate = (1.0 - _kalman_gain) * _err_estimate + fabs(_last_estimate - _current_estimate) * _q;
        _last_estimate = _current_estimate;
        return _current_estimate;
    }

    struct PID::State off_course(float normal, float current) {
        struct PID::State result;
        float absDelta = abs(normal - current);
        // Serial.println(absDelta);
        if (absDelta > 10) {
            result.st = PID::FATAL_ERROR;
        }

        if (absDelta < 0.8) result.isRotate = false;
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