#include "SerialIO.h"

#define DEBUG_SERIAL true

SerialIO IO;

struct Message currentMessage;

void setup() {
  IO = SerialIO();
}

void loop() {
  struct Message newMessage = IO.readMessage();
  if (newMessage.code != "") {
    handleMessage(newMessage);
  }
}

void handleMessage(struct Message message) {
  currentMessage = message;

  #if DEBUG_SERIAL
    echoMessageDebug(message);
  #endif

  if (message.type == COMMAND) {
    delay(2000);    // симуляция выполнения команды
    IO.sendCompletion();
  }
  else {
    delay(100);    // симуляция обработки данных с датчика
    struct Message outgoingMessage = IO.produceMessage(RESPONSE, "Hd", 120);
    IO.sendMessage(outgoingMessage);
  }
  
}

#if DEBUG_SERIAL
void echoMessageDebug(struct Message message) {
  
  Serial.println("Type: " + String(message.type));
  Serial.println("Code: " + message.code);
  Serial.print("Args:");
  for (int i = 0; i < IO.countArgs(message.args); i++) {
    Serial.print(" " + String(message.args[i]));
  }
  Serial.println();
}
#endif
