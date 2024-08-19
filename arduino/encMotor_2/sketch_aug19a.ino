// энкодер и прерывания
#include <Arduino.h>
#include <EncButton.h>

#include "defs.h"
EncButton enc(CLK, DT);

int last_x = 0, last_y = 0;
const float angleTicks = MAX_TICK / (float)(headInputRight + abs(headInputLeft));

byte power = 140;

// int targetAngle = 0;
int targetTick = 0;
bool headLoopRunning = false;

void isr() {
  enc.tickISR();
}

void setup() {
  Serial.begin(9600);
  pinMode(45, OUTPUT);
  pinMode(47, OUTPUT);
  pinMode(49, OUTPUT);
  pinMode(22, INPUT_PULLUP);

  Serial.println("AngleTicks " + String(angleTicks));

  analogWrite(EN_Head, power);

  Serial.println("Debug 0");
  attachInterrupt(0, isr, CHANGE);
  attachInterrupt(1, isr, CHANGE);
  enc.setEncISR(true);

  Serial.println("Debug 1");
  zero();
  Serial.println("Debug 2");
  delay(1000);
  Serial.println("Debug 3");
  home();
  Serial.println("Debug 4");

}

bool endFlag = false;
bool flag = true;
unsigned long c = 0;

void loop() {
  check_position();

  headLoop();
  if (!headLoopRunning) {
     //Print();
  }
  
  if (flag && !headLoopRunning) {
    if (c == 0) {
      c = millis();
    }
    else {
      if (millis() - c >= 2000) {
        c = 0;
        int rnd = random(-150, 120);
        Serial.println("--- Enc " + String(enc.counter) + " Target "  + String(targetTick) + " New " + String(rnd));
        HeadRemote(rnd);
        Serial.println("Target " + String(targetTick) + " Running " + String(headLoopRunning));
        flag = false;
      }
    }
  }
}

bool isEnd() {
  return !digitalRead(END_CAP);
}

bool awaitStop = false;
int awaitStopEnc = 0;
long unsigned awaitStopTimer = 0;
bool awaitStopCompleted = false;
int smoothStart = 0;

void check_position() {
  enc.tick();
  if (isEnd()) {
    if (!endFlag) {
      targetTick = 0;
      last_x = headInputLeft;
      awaitStop = false;
      awaitStopCompleted = false;
      awaitStopTimer = 0;
      awaitStopEnc = 0;
      headLoopRunning = false;
      smoothStart = 0;
      endFlag = true;
    }
  }
  else {
    endFlag = false;
  }
}

void zero() {
  if (isEnd()) {
    last_x = headInputLeft;
    return;
  }

  analogWrite(EN_Head, power);
  while (!isEnd()) {
    digitalWrite(PIN_IN1_head, LOW);
    digitalWrite(PIN_IN2_head, HIGH);
  }
  digitalWrite(PIN_IN1_head, LOW);
  digitalWrite(PIN_IN2_head, LOW);

  last_x = headInputLeft;
}

void Print() {
  Serial.println("\tX:");Serial.print(last_x);Serial.print("\tCounter: ");Serial.print(enc.counter);Serial.print("\tTarTick: ");
  Serial.print(targetTick);
}

void home() {
  HeadRemote(0);
}

void headLoop() {
  if (!headLoopRunning) {
    return;
  }

  if (awaitStop) {
    if (enc.counter != awaitStopEnc || awaitStopTimer == 0) {
      awaitStopEnc = enc.counter;
      awaitStopTimer = millis();
    }
    else {
      if (millis() - awaitStopTimer > 100) {
        awaitStop = false;
        awaitStopEnc = 0;
        awaitStopTimer = 0;
        awaitStopCompleted = true;
        Serial.println("Await stop completed");
      }
    }
  }

  if (awaitStopCompleted) {
    awaitStopCompleted = false;
    if (abs(targetTick - enc.counter) < 5) {
      headLoopRunning = false;
      Serial.println("Return");
      return;
    }
  }

  if (!awaitStop) {
    int delta = targetTick - enc.counter;
    //Serial.println("Move " + String(delta));
    
    if (abs(delta) < 5) {
      Serial.println("Start await stop");
      digitalWrite(PIN_IN1_head, LOW);
      digitalWrite(PIN_IN2_head, LOW);
      delay(50);

      smoothStart = 0;
      awaitStop = true;
      awaitStopEnc = enc.counter;
      awaitStopTimer = millis();
      awaitStopCompleted = false;
    }
    else {
      bool dir = delta > 0;

      digitalWrite(PIN_IN1_head, dir ? HIGH : LOW);
      digitalWrite(PIN_IN2_head, dir ? LOW : HIGH);

      float smoothProgressPercent = 0;
      if (smoothStart == 0) {
        smoothStart = enc.counter;
      } 
      else if (abs(enc.counter - targetTick) < 100){
        int smoothTotal = abs(targetTick - smoothStart);
        int smoothProgress = abs(enc.counter - smoothStart);
        smoothProgressPercent = min((float)smoothProgress / smoothTotal, 1);
      }

      int _power = max(power * (1 - smoothProgressPercent), 80);
      Serial.println(String(_power));
      analogWrite(EN_Head, _power); 
    }
  }
}

void HeadRemote(int x) {

  int targetAngle = x - last_x;
  last_x = x;
  enc.counter = 0;
  targetTick = round(targetAngle * angleTicks);

  headLoopRunning = true;
  Serial.println("HeadRemote " + String(targetTick));
  // while (abs(enc.counter) < current_x) {
  //   enc.tick();
  //   Serial.print(enc.counter);Serial.print("\t");Serial.print(dir);Serial.print("\t");
  //   Serial.print(x);Serial.print("\t");Serial.println(last_x);
  //   digitalWrite(PIN_IN1_head, dir ? HIGH : LOW);
  //   digitalWrite(PIN_IN2_head, dir ? LOW : HIGH);
  //   analogWrite(EN_Head, power);
  // }
  // digitalWrite(PIN_IN1_head, LOW);
  // digitalWrite(PIN_IN2_head, LOW);
  // // analogWrite(EN_Head, 0);
  // last_x = x;
}