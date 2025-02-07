#include <Arduino.h>
#include <Wire.h>

#include <Multiservo.h>
// Задаём количество сервоприводов
constexpr uint8_t MULTI_SERVO_COUNT = 12;
// Создаём массив объектов для работы с сервомоторами
Multiservo multiservo[MULTI_SERVO_COUNT];

// Подключаем дальномеры
#include "Adafruit_VL53L0X.h"
#define LOX1_ADDRESS 0x30
#define LOX2_ADDRESS 0x31
#define LOXHead_ADDRESS 0x32

#include "Adafruit_VL53L1X.h"

#define SHT_LOX1 7
#define SHT_LOX2 6
#define SHT_LOXHead 8

Adafruit_VL53L0X lox1 = Adafruit_VL53L0X();
Adafruit_VL53L0X lox2 = Adafruit_VL53L0X();
Adafruit_VL53L1X loxHead = Adafruit_VL53L1X(SHT_LOXHead);

// this holds the measurement
VL53L0X_RangingMeasurementData_t measure1;
VL53L0X_RangingMeasurementData_t measure2;
VL53L0X_RangingMeasurementData_t measureHead;

// Подключаем голову
#include "Head.h"
Head head(&multiservo[7], &multiservo[8], &loxHead);

#include "Laser.h"
Laser laserF(&multiservo[10], &lox1, 10);
Laser laserB(&multiservo[9], &lox2, 9);

// Библиотека для работы с модулями IMU
#include "CompassRemote.h"
CompassRemote compass;
struct CompassData compassData;

#include "motor.h"
motor wheels(&laserF, &laserB, &compass);

#include "Containers.h"
Containers up_front(&multiservo[2], UP_FRONT);
Containers up_back(&multiservo[3], UP_BACK);
Containers down(&multiservo[4], DOWN);
Containers drawerFront(&multiservo[DRAWER_FRONT], DRAWER_FRONT, drawerFrontSensor);

#include "RotationPID.h"
RotationPID pid;

#define DEBUG_SERIAL true

#include "SerialIO.h"
SerialIO IO;

struct Message currentMessage;

bool getReady = false;

uint16_t dist;

int lastHead;
unsigned long tmr;

#include "Touch.h"
Touch touchFront = Touch(FRONT_SENSOR);
Touch touchBack = Touch(BACK_SENSOR);

void setID() {
  pinMode(SHT_LOX1, OUTPUT);
  pinMode(SHT_LOX2, OUTPUT);
  // pinMode(SHT_LOXHead, OUTPUT);
  digitalWrite(SHT_LOX1, LOW);
  digitalWrite(SHT_LOX2, LOW);
  // digitalWrite(SHT_LOXHead, LOW);

  // all reset
  digitalWrite(SHT_LOX1, LOW);
  digitalWrite(SHT_LOX2, LOW);
  // digitalWrite(SHT_LOXHead, LOW);
  delay(10);
  // all unreset
  digitalWrite(SHT_LOX1, HIGH);
  digitalWrite(SHT_LOX2, HIGH);
  // digitalWrite(SHT_LOXHead, HIGH);
  delay(10);

  // activating LOX1 and resetting LOX2
  digitalWrite(SHT_LOX1, HIGH);
  digitalWrite(SHT_LOX2, LOW);
  // digitalWrite(SHT_LOXHead, LOW);
  delay(10);

  // initing LOX1
//  if (!lox1.begin(LOX1_ADDRESS)) {
//    Serial.println(F("Failed to boot FRONT VL53L0X"));
//    while (1);
//  }
  delay(10);

  // activating LOX2
  digitalWrite(SHT_LOX2, HIGH);
  // digitalWrite(SHT_LOXHead, LOW);
  delay(10);

  // initing LOX2
  // if (!lox2.begin(LOX2_ADDRESS)) {
  //   Serial.println(F("Failed to boot BACK VL53L0X"));
  //   while (1);
  // }
  delay(10);

  // digitalWrite(SHT_LOXHead, HIGH);
  delay(10);

  // initing LOXHEAD
  // if (!loxHead.begin(LOXHead_ADDRESS)) {
  //   Serial.println(F("Failed to boot HEAD VL53L0X"));
  //   while (1)
  //     ;
  // }

  Wire.begin();
  if (!loxHead.begin(LOXHead_ADDRESS, &Wire)) {
    Serial.print("Couldn't start ranging: ");
    Serial.println(loxHead.vl_status);
    while (1)       delay(10);
  }
  Serial.println("[SET ID] LOX Head OK");

  if (! loxHead.startRanging()) {
    Serial.print("[SET ID] Couldn't start ranging: ");
    Serial.println(loxHead.vl_status);
    while (1)       delay(10);
  }
  Serial.println("[SET ID] Ranging started");
}

void scanI2C() {
  int nDevices = 0;

  Serial.println("Scanning...");

  for (byte address = 1; address < 127; ++address) {
    // The i2c_scanner uses the return value of
    // the Wire.endTransmission to see if
    // a device did acknowledge to the address.
    Wire.beginTransmission(address);
    byte error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.print(address, HEX);
      Serial.println("  !");

      ++nDevices;
    } else if (error == 4) {
      Serial.print("Unknown error at address 0x");
      if (address < 16) {
        Serial.print("0");
      }
      Serial.println(address, HEX);
    }
  }
  if (nDevices == 0) {
    Serial.println("No I2C devices found\n");
  } else {
    Serial.println("done\n");
  }
}

void setup() {
  Serial.begin(9600);
  IO = SerialIO();

  compass.init();
  Serial.println("[SETUP] Compass begin OK");

  // Перебираем значения моторов от 0 до 11 (3 ящика, 2 лидара, 2 сервы в голове)
  /*
    * 2 - ящщик 1
    * 3 - ящик 2
    * 4 - ящик 3
    * 5 - выдвижной ящик зад
    * 6 - выдвижной ящик перед
    * 7 - голова по Y
    * 8 - тормооз для головы по Y
    * 9 - лидар 1
    * 10 - лидар 2
  */
  for (int count = 2; count < MULTI_SERVO_COUNT; count++) {
    // Не подключаем задний выдвижной
    if (count == DRAWER_BACK) {
      continue;
    }
    multiservo[count].attach(count);
  }
  multiservo[11].detach(); // детач Y головы

  multiservo[DRAWER_FRONT].write(97);    // остановка переднего выдвижного
  

  // Маленькие ящики в закрытое положение
  up_front.begin();
  up_back.begin();
  down.begin();
  drawerFront.begin();

  Serial.println("[SETUP] Servo attach OK");

  wheels.begin();
  Serial.println("[SETUP] wheels.begin() OK");

  Serial.println("[SETUP] Adafruit VL53L0X ID setup");
  setID();
  Serial.println("[SETUP] Adafruit VL53L0X ID OK");

  // loxHead.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_DEFAULT);
  // Serial.println("[SETUP] L0X HEAD config OK");

  // lox1.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_LONG_RANGE);
  Serial.println("[SETUP] L0X FORWARD config OK");

  // lox2.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_LONG_RANGE);
  Serial.println("[SETUP] L0X BACKWARD config OK");

  // laserF.begin();
  // laserB.begin();
  Serial.println("[SETUP] Laser.begin() OK");

  head.begin();
  Serial.println("[SETUP] Head.begin() OK");

  wheels.setSpeed(255, ALL);

  Serial.println("[SETUP] Going home...");
  head.home();
  Serial.println("HOME");
  getReady = false;

  scanI2C();
  Serial.println("[SETUP] Setup OK");
}

unsigned long loopTime, totalLoopTime;

void loop() {
  loopTime = millis();
  head.tick();
  // laserF.tick();
  // laserB.tick();
  
  touchFront.tick();
  touchBack.tick();

  up_front.tick();
  up_back.tick();
  down.tick();

  wheels.setBlocked(touchFront.isTouched() || touchBack.isTouched());
  wheels.tick();

  // pid.setSpeed();
  // wheels.setSpeed4(pid.BL, pid.BR, pid.FL, pid.FR);

  if (head.isCompleted()) {
    if (!getReady) {
      // Serial.println("READY");
      getReady = true;
    }
    struct Message outgoingMessage = IO.produceMessage(COMMAND, "Ph", head.currentX, head.sendY);
    IO.sendMessage(outgoingMessage);
    IO.sendCompletion();
  }
  if (wheels.isCompleted()) {
    IO.sendCompletion();
    Serial.println("OK WHEELS");
    wheels.clearState();
  }

  if (up_front.isCompleted() || up_back.isCompleted() || down.isCompleted()) {
    IO.sendCompletion();
  }

  struct Message newMessage = IO.readMessage();
  if (newMessage.code != "") {
    handleMessage(newMessage);
  }
  totalLoopTime = millis() - loopTime;
}

void handleMessage(struct Message message) {
  currentMessage = message;

  // #if DEBUG_SERIAL
  //     echoMessageDebug(message);
  // #endif
  if (message.type == COMMAND) {
    Serial.println(message.code);

    if (message.code == "H") {          // Движение головой на (x, y)
      IO.sendConfirmation();
      head.rotate(message.args[0], message.args[1]);
    } 
    else if (message.code == "Hi") {    // Движение головой по направлению
      IO.sendConfirmation();
      head.rotateXInf(message.args[0]);
    } 
    else if (message.code == "S") {     // Движение головой остановка
      IO.sendConfirmation();
      head.stop();
    } 
    else if (message.code == "L") {     // Лидары вкл./выкл.
      IO.sendConfirmation();
      if (message.args[0] == 0) {
        // laserF.scanStop();
        // laserB.scanStop();
      }
      else {
        // laserF.scanStart();
        // laserB.scanStart();
      }
    } 
    else if (message.code == "M") {     // Движение робота на (x, y)
      IO.sendConfirmation();
      wheels.run(message.args[0], message.args[1]);
    }
    else if (message.code == "Rot") {     // Вращение. 0 - стоп; >0 - по часовой; <0 - против часовой
      IO.sendConfirmation();
      if (message.args[0] == 0) wheels.go(Stop);
      else if  (message.args[0] < 0) wheels.go(RotateL);
      else wheels.go(RotateR);
    } 
    else if (message.code == "C") {     // Управление контейнерами
      IO.sendConfirmation();
      BoxMove(message.args[0], message.args[1]);
    } 
    else if (message.code == "Srv") {     // Ручная отправка углов на сервы
      IO.sendConfirmation();
      multiservo[message.args[0]].write(message.args[1]);
    } 
    else if (message.code == "Mt") {    // Движение робота по времени
      // R 89 / 10
      // L 110 / 10
      IO.sendConfirmation();
      wheels.go(message.args[0]);
      delay(message.args[1]);
      wheels.go(Stop);
    } 
    else if (message.code == "Te") {
      IO.sendConfirmation();
      multiservo[11].attach(11);

      multiservo[8].attach(8);
      multiservo[8].write(60);
      delay(500);
      multiservo[8].detach();

      multiservo[11].write(message.args[0]);

      multiservo[8].attach(8);
      multiservo[8].write(80);
      delay(500);
      multiservo[8].detach();

      multiservo[11].detach();
    }
    else if (message.code == "Mr") {
      // 181 181 178 178 (FL, FR, BL, BR)
      // SpeedLeft 110/10 = 11 cm/c
      IO.sendConfirmation();
      wheels.setSpeed(message.args[2], BL);
      wheels.setSpeed(message.args[3], BR);
      wheels.setSpeed(message.args[0], FL);
      wheels.setSpeed(message.args[1], FR);

      wheels.go(Right);
      delay(5000);
      wheels.go(Stop);
    } 
    else if (message.code == "Ml") {
      IO.sendConfirmation();
      wheels.setSpeed(message.args[2], BL);
      wheels.setSpeed(message.args[3], BR);
      wheels.setSpeed(message.args[0], FL);
      wheels.setSpeed(message.args[1], FR);
      wheels.go(Left);
      delay(5000);
      wheels.go(Stop);
    } 
    else if (message.code == "SE") {
      // 60 закрыто
      // 80 открыто
      IO.sendConfirmation();
      multiservo[8].write(message.args[0]);
    } 
    else if (message.code == "P") {     // Ввод текущих координат робота
      IO.sendConfirmation();
      wheels.setCurrentPosition(message.args[0], message.args[1]);
    }
    else if (message.code == "Sc") {     // корректировка скорости
      IO.sendConfirmation();
      wheels.setSpeedCorrection(message.args[0]);
    }
    else {
      Serial.println("Unknown code: " + message.code);
    }
  } else {
    if (message.code == "Hd") {
      IO.sendConfirmation();
      dist = head.getDistance();
      struct Message outgoingMessage = IO.produceMessage(RESPONSE, "Hd", dist);
      IO.sendMessage(outgoingMessage);
    }
    else if (message.code == "P") {
      IO.sendConfirmation();
      struct Message outgoingMessage = IO.produceMessage(RESPONSE, "P", wheels.currentX, wheels.currentY);
      IO.sendMessage(outgoingMessage);
    }
  }
}

// #if DEBUG_SERIAL
// void echoMessageDebug(struct Message message) {

//     Serial.println("Type: " + String(message.type));
//     Serial.println("Code: " + message.code);
//     Serial.print("Args:");
//     for (int i = 0; i < IO.countArgs(message.args); i++) {
//         Serial.print(" " + String(message.args[i]));
//     }
//     Serial.println();
// }
// #endif

void BoxMove(int index, int side) {
    BoxState targetState;
    switch(side) {
        case 0: targetState = CLOSE; break;
        case 1: targetState = OPEN_LEFT; break;
        case 2: targetState = OPEN_RIGHT; break;
    }
    switch (index) {
        case 0: down.set_position(targetState); break;
        case 1: up_back.set_position(targetState); break;
        case 2: up_front.set_position(targetState); break;
        case 3: drawerFront.togleTablet(targetState); break;
        case 4: break;
    }
}
