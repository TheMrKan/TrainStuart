// энкодер и прерывания
#include <Arduino.h>
#include <EncButton.h>

#include "defs.h"
EncButton enc(CLK, DT);

int last_x = 0, last_y = 0;
// int angleTicks = MAX_TICK / (headInputRight + headInputLeft);
int angleTicks = 3;

void isr() {
  enc.tickISR();
}

void setup() {
  Serial.begin(115200);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);

  Serial.println("Debug 0");
  attachInterrupt(0, isr, CHANGE);
  attachInterrupt(1, isr, CHANGE);
  enc.setEncISR(true);

  digitalWrite(7, LOW);
  analogWrite(6, 255);
  delay(500);
  analogWrite(6, 0);
  Serial.println("Debug 1");

  HeadRemote(90);

}

void loop() {
  HeadRemote(0);
  delay(2000);
  HeadRemote(180);
  delay(2000);
  HeadRemote(-180);
  delay(2000);
}

void HeadRemote(int x) {

  int current_x = x - last_x;
  bool dir;
  if (current_x > 0) dir = true;
  else dir = false;

  current_x = abs(current_x) * angleTicks;
  enc.counter = 0;
  while (abs(enc.counter )< current_x) {
    enc.tick();
    Serial.print(enc.counter);Serial.print("\t");Serial.print(dir);Serial.print("\t");
    Serial.print(x);Serial.print("\t");Serial.println(last_x);
    digitalWrite(PIN_IN1_head, dir ? LOW : HIGH);
    analogWrite(EN_Head, 150);
  }
  analogWrite(EN_Head, 0);
  last_x = x;
}

