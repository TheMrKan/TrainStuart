#include "Arduino.h"

class SerialIO {
  public:
    SerialIO();
    struct Message readMessage();
    void sendMessage(struct Message message);
    struct Message produceMessage(byte type, String code);

  private:
    String buffer = "";
    String readSerial();
    struct Message parseMessage(String newMessage);
};

struct Message {
  byte type;
  String code;
  int args[10];
};