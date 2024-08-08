#include "SerialIO.h"

SerialIO IO;

struct Message currentMessage;

void setup() {
  IO = SerialIO();
}

void loop() {
  struct Message newMessage = IO.readMessage();
  if (newMessage.code != "") {
    handleMessage(newMessage);
    struct Message outgoingMessage = IO.produceMessage(1, "Hd");
    outgoingMessage.args[0] = 120;
    IO.sendMessage(outgoingMessage);
    
  }
}

void handleMessage(struct Message message) {
  currentMessage = message;
  Serial.println("Type: " + String(message.type));
  Serial.println("Code: " + message.code);
  Serial.print("Args:");
  for (int i = 0; i < 10; i++) {
    Serial.print(" " + String(message.args[i]));
  }
  Serial.println();
}
