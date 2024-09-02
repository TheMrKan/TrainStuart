#include <Arduino.h>

#include <Multiservo.h>
// Задаём количество сервоприводов
constexpr uint8_t MULTI_SERVO_COUNT = 10;
// Создаём массив объектов для работы с сервомоторами
Multiservo multiservo[MULTI_SERVO_COUNT];

// Подключаем дальномеры
// #include "Sensor.h"
// Sensor sensor;
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
Head head(&multiservo[7]);

#include "motor.h"
motor wheels;

#include "SerialIO.h"

#define DEBUG_SERIAL true

SerialIO IO;

struct Message currentMessage;

bool getReady = false;

int dist;

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
  if(!lox1.begin(LOX1_ADDRESS)) {
    Serial.println(F("Failed to boot first VL53L0X"));
    while(1);
  }
  delay(10);

  // activating LOX2
  digitalWrite(SHT_LOX2, HIGH);
  digitalWrite(SHT_LOXHead, LOW);
  delay(10);

  //initing LOX2
  if(!lox2.begin(LOX2_ADDRESS)) {
    Serial.println(F("Failed to boot second VL53L0X"));
    while(1);
  }
  delay(10);

  digitalWrite(SHT_LOXHead, HIGH);
  delay(10);

  // if(!loxHead.begin(LOXHead_ADDRESS)) {
  //   Serial.println(F("Failed to boot second VL53L0X"));
  //   while(1);
  // }
  if (!loxHead.begin()) {
    Serial.println(F("Failed to boot HEAD VL53L0X"));
    while(1);
  }
}

void setup() {
    Serial.begin(115200);
    IO = SerialIO();

    // Перебираем значения моторов от 0 до 9
    for (int count = 2; count < MULTI_SERVO_COUNT; count++) {
        // Подключаем сервомотор
        multiservo[count].attach(count);
    }
    multiservo[7].detach();
    wheels.begin();
    Serial.println("Adafruit VL53L0X test");
    setID();
    Serial.println(String(getDistanse(0)) + "  " + String(getDistanse(1)) + "  " + String(getDistanse(2)));
    head.begin();
    wheels.setSpeed(200, ALL);
    head.home();

    getReady = false;
}

void loop() {
    head.tick();
    wheels.tick();
    dist = getDistanse(0);

    if (head.getState('x') && head.getState('y')) {
      if (!getReady) {
        Serial.println("READY");
        getReady = true;
      }
      else IO.sendCompletion();
    }
    struct Message newMessage = IO.readMessage();
    if (newMessage.code != "") {
        handleMessage(newMessage);
    }
}

void handleMessage(struct Message message) {
    currentMessage = message;

  // #if DEBUG_SERIAL
  //     echoMessageDebug(message);
  // #endif

    if (message.type == COMMAND) {
        Serial.println(message.code);
        if (message.code == "H") {
          head.rotate(message.args[0], message.args[1]);
        }
        if (message.code == "S") {
          head.stop();
        }
        if (message.code == "Hd") {
          Serial.println(getDistanse(message.args[0]));
        }
        if (message.code == "M") {
          Serial.println(message.args[0]);
          // if (message.args[0] == 1) {
          //   wheels.go(Forward);
          //   delay(12000);
          //   wheels.go(Stop);
          // }
          wheels.run(message.args[0], message.args[1]);
        }
    }
    else {
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

int getDistanse(int index) {
  lox1.rangingTest(&measure1, false); // pass in 'true' to get debug data printout!
  lox2.rangingTest(&measure2, false); // pass in 'true' to get debug data printout!
  loxHead.rangingTest(&measureHead, false); // pass in 'true' to get debug data printout!


  if (index == 1) {
    if(measure1.RangeStatus != 4) {     // if not out of range
      return measure1.RangeMilliMeter;
    } else return 0;
  } else if (index == 2) {
    if(measure2.RangeStatus != 4) {     // if not out of range
      return measure2.RangeMilliMeter;
    } else return 0;
  } else if (index == 0) {
    if(measureHead.RangeStatus != 4) {  // if not out of range
      return measureHead.RangeMilliMeter;
    } else return 0;
  }
}