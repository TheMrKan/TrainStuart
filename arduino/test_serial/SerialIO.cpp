#include "Arduino.h"
#include "SerialIO.h"

SerialIO::SerialIO() {
  Serial.begin(9600);
}

const char REQUEST_PREFIX = '?';
const int INT_MIN = -pow(2, 15) + 1;

// читает один символ из
struct Message SerialIO::readMessage() {
  struct Message result;

  String newMessage = readSerial();
  if (newMessage != "") {
    result = parseMessage(newMessage);
  }

  return result;
}

struct Message SerialIO::produceMessage(byte type, String code) {
  struct Message result;
  result.type = type;
  result.code = code;
  for (int i = 0; i < 10; i++) {
    result.args[i] = INT_MIN;
  }
  return result;
}

void SerialIO::sendMessage(struct Message message) {
  if (message.type == 1) {
    Serial.print('!');
  }
  Serial.print(message.code);
  for (int i = 0; i < 10; i++) {
    if (message.args[i] == INT_MIN) {
      break;
    }
    Serial.print(" ");
    Serial.print(String(message.args[i]));
  }
  Serial.println();
}

// читает все символы до '\n' и добавляет их в буффер. Если символ означает конец команды - возвращает всю команду БЕЗ ЭТОГО СИМВОЛА.
String SerialIO::readSerial() {
  while (Serial.available()) {
    char symbol = char(Serial.read());

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
  struct Message output = produceMessage(0, "");
  if (message == "") {
    return output;
  }

  int offset = 0;
  if (message.charAt(0) == REQUEST_PREFIX) {
    output.type = 1;
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
    output.args[argIndex++] = argStr.toInt();
  }

  return output;
}