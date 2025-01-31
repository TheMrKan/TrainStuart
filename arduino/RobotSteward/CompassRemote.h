#ifndef ADUINO_Compass_H
#define ADUINO_Compass_H

struct CompassData {
  bool isReady;
  int delta;
};

class CompassRemote {
public:
  CompassRemote() {}
  void init() {
    Serial2.begin(9600);
    on();
  }

  void tick() {
    while (Serial2.available()) {
      char symbol = char(Serial2.read());

      if (symbol == '\n') {
        String _buffer = buffer;
        buffer = "";
        data.delta = _buffer.toInt();
        data.isReady = true;
        // Serial.println("COMPASS <<< " + _buffer);
      }
      else if (isDigit(symbol) || symbol == '-') {
          buffer += symbol;
      }
      else {
        Serial.print(String(symbol));
      }
    }
  }

  void on() {
    Serial.println("------------------- ON --------------");
    Serial2.println("on");
  }

  void off() {
    Serial2.println("off");
  }

  struct CompassData readData() {
    struct CompassData _data = data;
    data.isReady = false;
    return _data;
  }
private:
  CompassData data;
  String buffer = "";
};

#endif