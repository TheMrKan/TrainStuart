//
// Created by Nikit on 22.08.2024.
//

#ifndef ADUINO_DEFS_H
#define ADUINO_DEFS_H

#define ENA_1 5       // ШИМ первого мотора
#define PIN_IN1_1 39  // Вывод управления направлением вращения мотора №1 FL
#define PIN_IN2_1 37  // Вывод управления направлением вращения мотора №1 FL

#define ENB_1 4       // ШИМ второго мотора
#define PIN_IN3_1 43  // Вывод управления направлением вращения мотора №2 FR
#define PIN_IN4_1 41  // Вывод управления направлением вращения мотора №2 FR

#define ENA_2 44      // ШИМ третьего мотора
#define PIN_IN1_2 38  // Вывод управления направлением вращения мотора №3 BL
#define PIN_IN2_2 40  // Вывод управления направлением вращения мотора №3 BL

#define ENB_2 46      // ШИМ четвертого мотора
#define PIN_IN3_2 48  // Вывод управления направлением вращения мотора №4 BR
#define PIN_IN4_2 42  // Вывод управления направлением вращения мотора №4 BR

#define RELE_1 14
#define RELE_2 15

#define SENSOR_DRAVER_1  24   // Нулевая точка ящика у аккумулятора
#define SENSOR_DRAVER_2  23   // Нулевая точко ящика у ардуино

#define EN_Head 45        // ШИМ мотора головы
#define PIN_IN1_head 49   // Вывод управления направлением вращения мотора головы
#define PIN_IN2_head 47   // Вывод управления направлением вращения мотора головы


// I2C адресса для переднего и заднего дальномеров
#define LOX1_ADDRESS 0x30
#define LOX2_ADDRESS 0x31
#define LOXHead_ADDRESS 0x32

// Пины адрессов для переднего и заднего дальномеров
#define SHT_LOX1 7
#define SHT_LOX2 6
#define SHT_LOXHead 8


// Углы для сервоприводов
#define UpFront_Right  165
#define UpFront_Center 117
#define UpFront_Left   65

#define UpBack_Right   0
#define UpBack_Center  62
#define UpBack_Left    110

#define Down_Right     40
#define Down_Center    98
#define Down_Left      150


//  Бошка
#define HeadCenter 60
#define HeadUp     179
#define HeadDown   10
// #define HeadCenter 90
// #define HeadUp     169
// #define HeadDown   60

#define headInputUp   20
#define headInputDown -20

#define headInputRight 160
#define headInputLeft  -165

// Подключаем энкодер
// #define CLK 2
// #define DT  3
const byte CLK = 2;
const byte DT = 3;
#define END_CAP 22 // Коневик на голову
#define FRONT_SENSOR A14 // Передний датчик
#define BACK_SENSOR A15  // Задний датчик

#define MAX_TICK 11090

#endif //ADUINO_DEFS_H
