// энкодер и прерывания
#include <Arduino.h>
#include <EncButton.h>
#include "SerialIO.h"

#include "defs.h"
EncButton enc(CLK, DT);

int last_x = 0, last_y = 0;
const float angleTicks = MAX_TICK / (float)(headInputRight + abs(headInputLeft));

byte power = 140;

SerialIO IO;

// int targetAngle = 0;
int targetTick = 0;
bool headLoopRunning = false;

struct Message message;


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

void handleMessage() {
  if (message.code == "H") {
    HeadRemote(message.args[0]);
  }
}

void loop() {
  check_position();

  headLoop();

  message = IO.readMessage();
  if (message.code != "") {
    handleMessage();
  }
}

bool isEnd() {
  return !digitalRead(END_CAP);
}

bool endFlag = false;

void check_position() {
  enc.tick();
  if (isEnd()) {
    if (!endFlag) {
      targetTick = 0;
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
    endFlag = true;
    return;
  }

  analogWrite(EN_Head, power);
  while (!isEnd()) {
    digitalWrite(PIN_IN1_head, LOW);
    digitalWrite(PIN_IN2_head, HIGH);
  }
  enc.counter = 0;
  digitalWrite(PIN_IN1_head, LOW);
  digitalWrite(PIN_IN2_head, LOW);

  last_x = headInputLeft;
  endFlag = true;
}

void Print() {
  Serial.println("\tX:");Serial.print(last_x);Serial.print("\tCounter: ");Serial.print(enc.counter);Serial.print("\tTarTick: ");
  Serial.print(targetTick);
}

void home() {
  HeadRemote(0);
}

bool awaitStop = false;
int awaitStopEnc = 0;
unsigned long awaitStopTimer = 0;
bool awaitStopCompleted = false;

int smoothStart = 0;

int bonusEnc = 0;
unsigned long bonusTimer = 0;
int bonusPower = 100;

const int MAX_DELTA = 2;

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
        //Serial.println("Await stop completed");
      }
    }
  }

  int delta = targetTick - enc.counter;
  if (awaitStopCompleted) {
    awaitStopCompleted = false;
    if (abs(delta) < MAX_DELTA) {
      headLoopRunning = false;
      //Serial.println("Return");
      return;
    }
  }

  if (!awaitStop) {
    
    //Serial.println("Move " + String(delta));
    
    if (abs(delta) < MAX_DELTA) {
      //Serial.println("Start await stop");
      digitalWrite(PIN_IN1_head, LOW);
      digitalWrite(PIN_IN2_head, LOW);
      delay(50);

      smoothStart = 0;
      awaitStop = true;
      awaitStopEnc = enc.counter;
      awaitStopTimer = millis();
      awaitStopCompleted = false;

      bonusPower = 100;
      bonusEnc = 0;
      bonusTimer = 0;
    }
    else {
      bool dir = delta > 0;

      digitalWrite(PIN_IN1_head, dir ? HIGH : LOW);
      digitalWrite(PIN_IN2_head, dir ? LOW : HIGH);

      float smoothProgressPercent = 0;
      if (smoothStart == 0) {
        smoothStart = enc.counter;
      } 
      else if (abs(delta) < 100) {
        int smoothTotal = abs(targetTick - smoothStart);
        int smoothProgress = abs(enc.counter - smoothStart);
        smoothProgressPercent = max(min((float)smoothProgress / smoothTotal, 1), 0.1) * 0.8;
      }
      else if (abs(delta) < 200) {
        smoothProgressPercent = 0.2;
      }

      if (bonusTimer == 0 || enc.counter != bonusEnc) {
        bonusEnc = enc.counter;
        bonusTimer = millis();
      }
      else if (millis() - bonusTimer > 200) {
        bonusPower = min(100, max(70, map(delta, 0, 200, 70, 100)));
        bonusEnc = enc.counter;
        bonusTimer = millis();
      }

      int _power = min(max(power * (1 - smoothProgressPercent), 50) + bonusPower, 150);
      bonusPower = max(0, bonusPower - 5);
      Serial.println(String(_power) + " " + String(bonusPower) + " " + String(targetTick) + " " + String(enc.counter));

      analogWrite(EN_Head, _power); 
    }
  }
}

void HeadRemote(int x) {

  last_x += round(enc.counter / angleTicks);
  int targetAngle = x - last_x;
  Serial.println("Enc " + String(enc.counter) + " " + String(last_x));
  enc.counter = 0;
  targetTick = round(targetAngle * angleTicks);

  headLoopRunning = true;
  Serial.println("HeadRemote " +  String(targetTick));
}