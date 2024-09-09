#include <Arduino.h>

#include "Adafruit_VL53L0X.h"

#include <Multiservo.h>


/* side
 * 1 - left
 * 2 - center
 * 3 - right
*/

enum L {
  FRONT,
  BACK
};

class Laser {
  public:
    Laser(Multiservo* _servo, Adafruit_VL53L0X* _lox, L _type) {
      servo = _servo;
      type = _type;
      lox = _lox;
    }
    void begin() {
      int pin;
      servo->write(60);
      lox->startRangeContinuous();
      // if (!lox.begin()) {
      //   Serial.println(F("Failed to boot VL53L0X"));
      //   while(1);
      // }
    }
    int getSide() {
      if (side != 0) {
        int s = side;
        side = 0;
        return s;
      } else return 0;
    }
    void scan() {
      if (millis() - tmr >= 5) {
        // Serial.println("Debug 1");
        tmr = millis();
        if (dir && currentAngle == right) {
          dir = false;
          index = right;
        }
        else if (!dir && currentAngle == left) {
          index = 0;
          dir = true;
          ++isPeriod;
          flag = true;
        }

        if (flag) {
          flag = false;
          // for (int i=0; i<=lenArray; i++) {
          //   if (array1[i] != 0 && array1[i] != 8190) {
          //     int s1=0, s2=0, s3=0, s4=0;
          //     int k1=0, k2=0, k3=0, k4=0;
          //     if (i >= 0 && i < 45) { s1 += array1[i];}
          //     if (i >= 45 && i < 90) { s2 += array1[i]; }
          //     if (i >= 90 && i < 135) { s3 += array1[i]; }
          //     if (i >= 135 && i <= 180) { s4 += array1[i]; }
          //     Serial.println(String(s1/45) + " " + String(s2/45) + " " + String(s3/45) + " " + String(s4/45));
          //     Serial.print(String(array1[i]) + " ");
          //   }
              
          // }
          int s1=0, s2=0, s3=0, s4=0;
          for (int i=0; i< 45; i++) {
            
            if (array1[i] != 0 && array1[i] != 8190) {
              s1+=array1[i];
            }
          }
          
          Serial.println(s1/45);
          Serial.println();
        }

        // if (isPeriod == 3) {
        //   isPeriod = 0;
        //   // Тут нужна обработка массива показаний датчика
        //   // Будет определяться где препятствие
        //   for (int i = 0; i <= lenArray; ++i) {
        //     float avr = (array1[i] + array2[i] + array3[i]) / 3;
        //     array[i] = avr;
        //   }

        //   for (int i = 0; i <= lenArray; ++i) {
        //     bool j = array[i] >= maxDist;
        //     if (i < round(lenArray/3)) {
        //       if (j) side = 1;
        //     }
        //     else if (i > lenArray - round(lenArray/3*2)) {
        //       if (j) side = 3;
        //     }
        //     else {
        //       if (j) side = 2;
        //     }
        //   }
        // }

        if (dir && currentAngle < right) {
          ++currentAngle;
          ++index;
          // Считывание дистанции
        }
        else if (!dir && currentAngle > left) {
          --currentAngle;
          ++index;
          // Считывание дистанции
        }
        // lox->rangingTest(&measure, false);
        if (lox->isRangeComplete()) {
          array1[index] = lox->readRange();
          // Serial.println(lox->readRange());
          // if (isPeriod == 1) array1[index] = lox->readRange();
          // if (isPeriod == 2) array2[index] = lox->readRange();
          // if (isPeriod == 3) array3[index] = lox->readRange();
        }
        // if (measure.RangeStatus != 4) {
        //   if (isPeriod == 1) array1[index] = measure.RangeMilliMeter;
        //   if (isPeriod == 2) array2[index] = measure.RangeMilliMeter;
        //   if (isPeriod == 3) array3[index] = measure.RangeMilliMeter;
        // }
        servo->write(currentAngle);
        // Serial.println("SCAN" + String(currentAngle));
      }
    }
  private:
    L type;
    Multiservo* servo;
    Adafruit_VL53L0X* lox;
    VL53L0X_RangingMeasurementData_t measure;
    static const int left = 70;
    static const int right = 160;

    bool dir = true, flag = false;
    int currentAngle = 0, index = 0, isPeriod = 0;
    unsigned long tmr = 0;

    // Массив. Количество ячеек - это двойная разница углов
    static const int lenArray = (right - left) * 2;
    int array1[lenArray], array2[lenArray], array3[lenArray];
    float array[lenArray];

    const int maxDist = 200;

    int side;
};