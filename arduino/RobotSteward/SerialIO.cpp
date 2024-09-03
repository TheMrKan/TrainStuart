#include "Arduino.h"
#include "SerialIO.h"

#define IOSerial Serial

SerialIO::SerialIO() {
  IOSerial.begin(115200);
}

const char REQUEST_PREFIX = '?';

struct Message SerialIO::readMessage() {
  struct Message result;

  String newMessage = readSerial();
  if (newMessage != "") {
    result = parseMessage(newMessage);
    sendConfirmation();
  }

  return result;
}

struct Message SerialIO::produceMessage(byte type, String code, int a0, int a1, int a2, int a3, int a4, int a5, int a6, int a7, int a8, int a9) {
  struct Message result;
  result.type = type;
  result.code = code;
  result.args[0] = a0; result.args[1] = a1; result.args[2] = a2; result.args[3] = a3; result.args[4] = a4;
  result.args[5] = a5; result.args[6] = a6; result.args[7] = a7; result.args[8] = a8; result.args[9] = a9;
  return result;
}

void SerialIO::sendMessage(struct Message message) {
  if (message.type == RESPONSE) {
    IOSerial.print('!');
  }
  IOSerial.print(message.code);
  for (int i = 0; i < countArgs(message.args); i++) {
    IOSerial.print(" ");
    IOSerial.print(String(message.args[i]));
  }
  IOSerial.println();
}

void SerialIO::sendConfirmation() {
  IOSerial.println("+");
}

void SerialIO::sendCompletion() {
  IOSerial.println("OK");
}

int SerialIO::countArgs(int args[]) {
  for (int i = 0; i < 10; i++) {
    if (args[i] == INT_MIN) {
      return i;
    }
  }
  return 10;
}

// читает все символы до '\n' и добавляет их в буффер. Если символ означает конец команды - возвращает всю команду БЕЗ ЭТОГО СИМВОЛА.
String SerialIO::readSerial() {
  while (IOSerial.available()) {
    char symbol = char(IOSerial.read());

    if (symbol == '\n') {
      String _buffer = buffer;
      buffer = "";
      return _buffer;
    }

    buffer += symbol;
  }

  return "";
}


struct Message SerialIO::parseMessage(String message) {
  struct Message output = produceMessage(COMMAND, "");
  if (message == "") {
    return output;
  }

  int offset = 0;
  if (message.charAt(0) == REQUEST_PREFIX) {
    output.type = REQUEST;
    offset++;
  }

  bool isWritingArgs = false;
  String argStr = "";
  int argIndex = 0;
  for (int i = offset; i < message.length(); i++) {
    char c = message.charAt(i);

    if (isSpace(c)) {
      if (!isWritingArgs) {
        isWritingArgs = true;
      }
      else {
        output.args[argIndex++] = argStr.toInt();
        argStr = "";
      }
    }
    else {
      if (isWritingArgs) {
        argStr += c;
      }
      else {
        output.code += c;
      }
    }
  }

  if (argStr != "") {
    output.args[argIndex] = argStr.toInt();
  }

  return output;
}