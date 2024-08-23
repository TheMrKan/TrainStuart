//
// Created by Nikit on 22.08.2024.
//

#ifndef ADUINO_DEFS_H
#define ADUINO_DEFS_H

#define EN_Head 45        // ШИМ мотора головы
#define PIN_IN1_head 49   // Вывод управления направлением вращения мотора головы
#define PIN_IN2_head 47   // Вывод управления направлением вращения мотора головы


//  Бошка
#define HeadCenter 102
#define HeadUp     179
#define HeadDown   70

#define headInputUp   20
#define headInputDown -10

#define headInputRight 160
#define headInputLeft  -165

// Подключаем энкодер
// #define CLK 2
// #define DT  3
const byte CLK = 2;
const byte DT = 3;
#define END_CAP 22 // Коневик на голову

#define MAX_TICK 11090

#endif //ADUINO_DEFS_H
