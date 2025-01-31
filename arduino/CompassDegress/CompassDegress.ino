#include <SoftwareSerial.h>

// Библиотека для работы с модулями IMU
#include <TroykaIMU.h>

#include "RotationPID.h"
RotationPID pid;

// Создаём объект для работы с магнитометром/компасом
Compass compass;

// Калибровочные данные для работы магнитометра в режиме компаса
// Подробности читайте в документации про калибровку модуля
// http://wiki.amperka.ru/articles:troyka-magnetometer-compass-calibrate 
const float compassCalibrationBias[3] = { 567.893, -825.35, 1061.436 };

const float compassCalibrationMatrix[3][3] = { { 1.909, 0.082, 0.004 },
                                               { 0.049, 1.942, -0.235 },
                                               { -0.003, 0.008, 1.944} };

float start_angle, angle;
float filter, delta;
unsigned long tmr;

bool state = false;
float _err_measure = 0.8;  // примерный шум измерений
float _q = 0.1;   // скорость изменения значений 0.001-1, варьировать самому

String buffer = "";


void setup() {
    // Открываем последовательный порт
    Serial.begin(9600);
    // Выводим сообщение о начале инициализации
    Serial.println("Compass begin");
    pinMode(13, OUTPUT);
    digitalWrite(13, LOW);
    // Инициализируем компас
    compass.begin();
    // Устанавливаем калибровочные данные
    compass.setCalibrateMatrix(compassCalibrationMatrix,
                               compassCalibrationBias);
    
    // Выводим сообщение об удачной инициализации
    Serial.println("Initialization completed");
    readDeltaAngle(&start_angle);
    Serial.println("setConfig ok");
}

void loop() {
  String message = readSerial();
  
  if (message != "") {
    Serial.println("message " + message + ";");
    CompassOn();
  }

  if (state) {
    if (millis() - tmr >= 100) {
      tmr = millis();
      Serial.println(String(getDelta()));
    }
  }
}

String readSerial() {
  while (Serial.available()) {
    char symbol = char(Serial.read());
    // Serial.println(String(symbol));
    if (symbol == '\n') {
      String _buffer = buffer;
      buffer = "";
      // Serial.println(_buffer);
      return _buffer;
    }

    buffer += symbol;
  }

  return "";
}

void readDeltaAngle(float *angle) {
  *angle = compass.readAzimut();
}

void CompassOn() {
  state = true;
  Serial.println("CompassOn");
  readDeltaAngle(&start_angle);
  compass.sleep(false);
}

void CompassOff() {
  state = false;
  compass.sleep(true);
}

int getDelta() {
  readDeltaAngle(&angle);
  // return angle;
  return round(simpleKalman(angle - start_angle));
  // return start_angle;
}

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




