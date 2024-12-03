#include <Arduino.h>

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

#define SHT_LOX1 7
#define SHT_LOX2 6
#define SHT_LOXHead 8

Adafruit_VL53L0X lox1 = Adafruit_VL53L0X();
Adafruit_VL53L0X lox2 = Adafruit_VL53L0X();
Adafruit_VL53L0X loxHead = Adafruit_VL53L0X();

// this holds the measurement
VL53L0X_RangingMeasurementData_t measure1;
VL53L0X_RangingMeasurementData_t measure2;
VL53L0X_RangingMeasurementData_t measureHead;

// Подключаем голову
#include "Head.h"
Head head(&multiservo[7], &multiservo[8]);

#include "Laser.h"
// Laser laserF(&multiservo[9], &lox2, FRONT);
// Laser laserB(&multiservo[10], &lox1, BACK);
Laser laserF(&multiservo[10], &lox1, 10);
Laser laserB(&multiservo[9], &lox2, 9);

#include "motor.h"
motor wheels(&laserF, &laserB);
// motor wheels;

#include "SerialIO.h"

#define DEBUG_SERIAL true

SerialIO IO;

struct Message currentMessage;

bool getReady = false;

uint16_t dist;

int lastHead;
unsigned long tmr;

enum Box {
  DRAWER_BACK = 5,    // задний
  DRAWER_FRONT = 6,    // передний
  UP_BACK = 3,  // Задний
  UP_FRONT = 2,  //Передний
  DOWN = 4
};

enum State {
  CLOSE = 0,
  OPEN_LEFT = 1,
  OPEN_RIGHT = 2
};

State drawer1 = CLOSE;
State drawer2 = CLOSE;
State up_1 = CLOSE;
State up_2 = CLOSE;
State down = CLOSE;

void setID() {
  pinMode(SHT_LOX1, OUTPUT);
  pinMode(SHT_LOX2, OUTPUT);
  pinMode(SHT_LOXHead, OUTPUT);
  digitalWrite(SHT_LOX1, LOW);
  digitalWrite(SHT_LOX2, LOW);
  digitalWrite(SHT_LOXHead, LOW);

  // all reset
  digitalWrite(SHT_LOX1, LOW);
  digitalWrite(SHT_LOX2, LOW);
  digitalWrite(SHT_LOXHead, LOW);
  delay(10);
  // all unreset
  digitalWrite(SHT_LOX1, HIGH);
  digitalWrite(SHT_LOX2, HIGH);
  digitalWrite(SHT_LOXHead, HIGH);
  delay(10);

  // activating LOX1 and resetting LOX2
  digitalWrite(SHT_LOX1, HIGH);
  digitalWrite(SHT_LOX2, LOW);
  digitalWrite(SHT_LOXHead, LOW);
  delay(10);

  // initing LOX1
  if (!lox1.begin(LOX1_ADDRESS)) {
    Serial.println(F("Failed to boot first VL53L0X"));
    while (1)
      ;
  }
  delay(10);

  // activating LOX2
  digitalWrite(SHT_LOX2, HIGH);
  digitalWrite(SHT_LOXHead, LOW);
  delay(10);

  // initing LOX2
  if (!lox2.begin(LOX2_ADDRESS)) {
    Serial.println(F("Failed to boot second VL53L0X"));
    while (1)
      ;
  }
  delay(10);

  digitalWrite(SHT_LOXHead, HIGH);
  delay(10);

  // initing LOXHEAD
  if (!loxHead.begin(LOXHead_ADDRESS)) {
    Serial.println(F("Failed to boot HEAD VL53L0X"));
    while (1)
      ;
  }
}

void setup() {
  Serial.begin(9600);
  IO = SerialIO();

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
  multiservo[11].detach(); // 7 ???

  multiservo[DRAWER_FRONT].write(95);    // остановка переднего выдвижного

  // Маленькие ящики в закрытое положение
  multiservo[UP_FRONT].write(UpBack_Center);    // UpFront и UpBack перепутаны !!!
  multiservo[UP_BACK].write(UpFront_Center);

  Serial.println("[SETUP] Servo attach OK");

  wheels.begin();
  Serial.println("[SETUP] wheels.begin() OK");

  Serial.println("[SETUP] Adafruit VL53L0X ID setup");
  setID();
  Serial.println("[SETUP] Adafruit VL53L0X ID OK");

  loxHead.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_DEFAULT);
  Serial.println("[SETUP] L0X HEAD config OK");

  lox1.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_LONG_RANGE);
  Serial.println("[SETUP] L0X FORWARD config OK");

  lox2.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_LONG_RANGE);
  Serial.println("[SETUP] L0X BACKWARD config OK");

  // laserF.begin();
  // laserB.begin();
  // Serial.println("[SETUP] Laser.begin() OK");

  head.begin();
  Serial.println("[SETUP] Head.begin() OK");

  wheels.setSpeed(255, ALL);

  Serial.println("[SETUP] Going home...");
  head.home();
  getReady = false;

  Serial.println("[SETUP] Setup OK");
}

unsigned long loopTime, totalLoopTime;

void loop() {
  loopTime = millis();
  head.tick();
  laserF.tick();
  laserB.tick();
  wheels.tick();

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
    /*if (message.code != "M" && message.code != "Mt") {
      laserF.scanStop();
      laserB.scanStop();
    } else {
      laserF.scanStart();
      laserB.scanStart();
    }*/

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
        laserF.scanStop();
        // laserB.scanStop();
      }
      else {
        laserF.scanStart();
        // laserB.scanStart();
      }
    } 
    else if (message.code == "M") {     // Движение робота на (x, y)
      IO.sendConfirmation();
      wheels.run(message.args[0], message.args[1]);
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
    else if (message.code == "Ml") {
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
    else if (message.code == "Mr") {
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
    else {
      Serial.println("Unknown code: " + message.code);
    }
  } else {
    IO.sendConfirmation();
    dist = getDistanse();
    struct Message outgoingMessage = IO.produceMessage(RESPONSE, "Hd", dist);
    IO.sendMessage(outgoingMessage);
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

uint16_t getDistanse() {
  loxHead.rangingTest(&measureHead, false);
  if (measureHead.RangeStatus != 4) {
    return measureHead.RangeMilliMeter;
  }
}

void BoxMove(int index, int side) {
  Box box;
  State state;
  switch (index) {
    case 0: box = DOWN; break;
    case 1: box = UP_BACK; break;
    case 2: box = UP_FRONT; break;
    case 3: box = DRAWER_BACK; break;
    case 4: box = DRAWER_FRONT; break;
  }
  switch (side) {
    case 0: state = CLOSE; break;
    case 1: state = OPEN_RIGHT; break;
    case 2: state = OPEN_LEFT; break;
  }
  // Serial.println("Box mapped: " + String(box) + " " + String(state));


  switch (box) {  // Выполнение запрашиваемой функции
    case DRAWER_BACK:
    case DRAWER_FRONT:
      if (state == CLOSE) {
        int sensor;
        State drawer;
        if (box == DRAWER_BACK) {
          sensor = SENSOR_DRAVER_1;
          drawer = drawer1;
        } else {
          sensor = SENSOR_DRAVER_2;
          drawer = drawer2;
        }

        tmr = millis();
        while (millis() - tmr <= 4000) {
          if (digitalRead(sensor)) break;
          if (drawer == OPEN_RIGHT) multiservo[box].write(120);
          else if (drawer == OPEN_LEFT) multiservo[box].write(60);
        }
        multiservo[box].write(95);

        if (box == DRAWER_BACK) drawer1 = CLOSE;
        else drawer2 = CLOSE;
      } else if (state == OPEN_RIGHT) {
        
        tmr = millis();
        while (millis() - tmr <= 3000) multiservo[box].write(60);
        multiservo[box].write(95);

        if (box == DRAWER_BACK) drawer1 = OPEN_RIGHT;
        else drawer2 = OPEN_RIGHT;
      } else {

        tmr = millis();
        while (millis() - tmr <= 3000) multiservo[box].write(120);
        multiservo[box].write(95);

        if (box == DRAWER_BACK) drawer1 = OPEN_LEFT;
        else drawer2 = OPEN_LEFT;
      }
      IO.sendCompletion();
      break;


    case UP_FRONT:
      if (state == CLOSE) {
        if (up_2 == OPEN_RIGHT) {
          for (int i = UpBack_Right; i <= UpBack_Center; ++i) {
            multiservo[box].write(i);
            delay(30);
          }
        } else if (up_2 == OPEN_LEFT) {
          for (int i = UpBack_Left; i >= UpBack_Center; --i) {
            multiservo[box].write(i);
            delay(30);
          }
        } else multiservo[box].write(UpBack_Center);
        up_2 = CLOSE;
      } else if (state == OPEN_RIGHT) {
        for (int i = UpBack_Center; i >= UpBack_Right; --i) {
          multiservo[box].write(i);
          delay(30);
        }
        up_2 = OPEN_RIGHT;
      } else {
        for (int i = UpBack_Center; i <= UpBack_Left; ++i) {
          multiservo[box].write(i);
          delay(30);
        }
        up_2 = OPEN_LEFT;
      }
      IO.sendCompletion();
      break;


    case DOWN:
      if (state == CLOSE) {
        if (down == OPEN_RIGHT) {  //multiservo[box].read() == Down_Right
          for (int i = Down_Right; i <= Down_Center; ++i) {
            multiservo[box].write(i);
            delay(30);
          }
        } else if (down == OPEN_LEFT) {
          for (int i = Down_Left; i >= Down_Center; --i) {
            multiservo[box].write(i);
            delay(30);
          }
        } else multiservo[box].write(Down_Center);
        down = CLOSE;
      } else if (state == OPEN_RIGHT) {
        for (int i = Down_Center; i >= Down_Right; --i) {
          multiservo[box].write(i);
          delay(30);
        }
        down = OPEN_RIGHT;
      } else {
        for (int i = Down_Center; i <= Down_Left; ++i) {
          multiservo[box].write(i);
          delay(40);
        }
        down = OPEN_LEFT;
      }
      IO.sendCompletion();
      break;
  }
}