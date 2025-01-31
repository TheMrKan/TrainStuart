#ifndef ARDUINO_ALIGN_H
#define ARDUINO_ALIGN_H

#include "motor.h"
#include "Head.h"

enum Phase {
  None,
  RotatingHead,
  RotatingRight_1,
  RotatingRight_2,
  Final
};

class Align {

  public:
    Align(motor* _movement, Head* _head) {
      movement = _movement;
      head = _head;
    }

    void run(int headAngleX) {
      if (isRunning) {
        return;
      }

      isRunning = true;
      phase = RotatingHead;
      head->rotate(headAngleX, 0);
    }

    void tick() {
      if (!isRunning) {
        return;
      }

      switch (phase) {
        case None:
          return;

        case RotatingHead:
          if (!head->isCompleted()) {
            return;
          }

          phase = RotatingRight_2;
          phaseStart = millis();
          distanceHistoryLastWrite = 0;
          clearDistanceHistory();
          movement->go(RotateR);
          Serial.println("HEAD ROTATION COMPLETED");
          return;


        case RotatingRight_1:
          // if (millis() - phaseStart < 500) {
          //   if (millis() - distanceHistoryLastWrite >= 10) {
          //     unsigned int distance = head->getDistance();
          //     if (distance > 300) {
          //       appendDistanceToHistory(distance);
          //       distanceHistoryLastWrite = millis();
          //     }
          //   }
          //   return;
          // }

          // unsigned int start = getAvgHistoryHead(4);
          // unsigned int stop = getAvgHistoryTail(4);
          // unsigned int mn = getHistoryMin();

          // bool inRange = max(start - mn, stop - mn) > 100;
          // if (!inRange) {
          //   // едем к найденому минимуму
          //   return;
          // }
          return;
        case RotatingRight_2:


          unsigned int distance = head->getDistance();
          
          if (distance == 0 || (millis() - distanceHistoryLastWrite) < 20) {
            return;
          }

          appendDistanceToHistory(distance);

          Serial.println("DISTANCE " + String(distance));

          if (millis() - phaseStart <= 300) {
            return;
          }

          unsigned int mn = getHistoryMin();
          unsigned int tail = getAvgHistoryTail(1);

          Serial.println("MIN " + String(mn) + " TAIL " + String(tail));

          if (tail - mn > 50) {
              clearDistanceHistory();
              targetDistance = mn;
              phase = Final;
              movement->go(RotateL);
              Serial.println("TARGET DISTANCE " + String(targetDistance));
              return;
          }

          return;
      }

      if (phase == Final) {
          unsigned int distance2 = head->getDistance();
          if (distance2 == 0) {
            return;
          }

          Serial.println("DISTANCE FINAL " + String(distance2));

          if (abs(distance2 - targetDistance) < 1) {
            movement->go(Stop);
            phase = None;
            isRunning = false;
            return;
          }

          return;
      }
    }
    bool readState();

  private:
    motor* movement;
    Head* head;

    bool isRunning = false;
    unsigned long lastTick = 0;
    Phase phase = None;
    unsigned long phaseStart = 0;
    unsigned long targetDistance = 0;

    static const short HISTORY_LEN = 250;
    unsigned int distanceHistory[HISTORY_LEN];
    unsigned long distanceHistoryLastWrite;
    short distanceHistoryLastIndex;

    // заполняет историю нулями
    void clearDistanceHistory() {
      memset(distanceHistory, 0, HISTORY_LEN);
      distanceHistoryLastIndex = 0;
    }

    // ставит переданное значение в первый свободный "слот"
    void appendDistanceToHistory(int value) {
      distanceHistory[distanceHistoryLastIndex > 0 ? distanceHistoryLastIndex + 1 : distanceHistoryLastIndex] = value;
      distanceHistoryLastIndex++;
      distanceHistoryLastWrite = millis();
    }

    // сред. арифм. первых НЕ НУЛЕВЫХ len элементов
    // когда встречается первый 0, значит история еще не успела заполниться
    unsigned int getAvgHistoryHead(short len) {
      unsigned int sum = 0;
      short cnt = 0;    // кол-во элементов в сумме. Нужно на случай, если 0 встретился раньше len
      for (short i = 0; i < len; i++) {    // len должен быть меньше длины массива
        if (distanceHistory[i] == 0) {
          break;
        }
        sum += distanceHistory[i];
        cnt += 1;
      }

      if (cnt == 0) {
        return 0;
      }

      return round(sum / cnt);
    }

    unsigned int getAvgHistoryTail(short len) {
      unsigned int sum = 0;
      for (short i = distanceHistoryLastIndex; i > distanceHistoryLastIndex - len; i--)
      {
        if (distanceHistory[i] != 0) {
          sum += distanceHistory[i];
        }
      }

      return round(sum / len);
    }

    unsigned int getHistoryMin() {
      unsigned int mn = distanceHistory[0];
      for (short i = 1; i <= distanceHistoryLastIndex; i++) {
        if (distanceHistory[i] != 0 && distanceHistory[i] < mn) {
          mn = distanceHistory[i];
        }
      }
      return mn;
    }
};

#endif