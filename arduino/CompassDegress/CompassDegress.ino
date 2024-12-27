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

float start_z, z;
float filter, delta;


void setup() {
    // Открываем последовательный порт
    Serial.begin(9600);
    // Выводим сообщение о начале инициализации
    Serial.println("Compass begin");
    // Инициализируем компас
    compass.begin();
    // Устанавливаем калибровочные данные
    compass.setCalibrateMatrix(compassCalibrationMatrix,
                               compassCalibrationBias);
    
    // Выводим сообщение об удачной инициализации
    Serial.println("Initialization completed");
    readDeltaAngle(&start_z);
    pid.setConfig(start_z, 150, F);
    Serial.println("setConfig ok");
}

void loop() {
    // Выводим азимут относительно оси Z
    // Serial.print(compass.readAzimut());
    readDeltaAngle(&z);
    pid.setAngle(z);

    pid.setSpeed();
    // Serial.print(pid.currentState.delta);
    // Serial.print("\t");
    // Serial.print(pid.currentState.dir);
    // Serial.print("\t");
    // Serial.print(pid.currentState.st);
    // Serial.print("\t");
    // Serial.println(pid.currentState.isRotate);

    // filter = simpleKalman(delta);
    // Serial.print(-20);
    // Serial.print("\t");
    // Serial.print(20);
    // Serial.print("\t");
    // Serial.print(filter);
    // Serial.print("\t");
    // Serial.println(delta);
    // Serial.println(" Degrees");
    // delay(100);
}


void readDeltaAngle(float *angle) {
  *angle = compass.readAzimut();
}




