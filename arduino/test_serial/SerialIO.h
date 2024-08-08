#include "Arduino.h"

const byte COMMAND = 0;
const byte REQUEST = 1;
const byte RESPONSE = 1;
const int INT_MIN = -pow(2, 15) + 1;

class SerialIO {
  public:
    SerialIO();
    struct Message readMessage();
    void sendMessage(struct Message message);
    void sendConfirmation();
    void sendCompletion();
    int countArgs(int args[]);
    struct Message produceMessage(byte type, String code, 
                                  int a0 = INT_MIN, int a1 = INT_MIN, int a2 = INT_MIN, int a3 = INT_MIN, int a4 = INT_MIN,
                                  int a5 = INT_MIN, int a6 = INT_MIN, int a7 = INT_MIN, int a8 = INT_MIN, int a9 = INT_MIN);

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