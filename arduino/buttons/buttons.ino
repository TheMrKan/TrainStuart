/**
   BasicHTTPClient.ino

    Created on: 24.05.2015

*/

#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

#include <ESP8266HTTPClient.h>

#include <WiFiClient.h>

ESP8266WiFiMulti WiFiMulti;

#define BUTTON_PIN 4
#define BUTTON_NUMBER 2

void setup() {

  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  // Serial.setDebugOutput(true);

  Serial.println();
  Serial.println();
  Serial.println();

  for (uint8_t t = 4; t > 0; t--) {
    Serial.printf("[SETUP] WAIT %d...\n", t);
    Serial.flush();
    delay(1000);
  }

  WiFi.mode(WIFI_STA);
  WiFiMulti.addAP("TrainStuart", "WiFiPassword");
}

void loop() {
  // wait for WiFi connection
  if ((WiFiMulti.run() == WL_CONNECTED)) {

    WiFiClient client;

    HTTPClient http;

    int buttonState = digitalRead(BUTTON_PIN);
    if (buttonState == LOW) {

      Serial.print("[HTTP] begin...\n");
      if (http.begin(client, "http://192.168.137.1:8002/carriage/call/?button_id=" + String(BUTTON_NUMBER))) {  // HTTP

        http.addHeader("Content-Type", "application/json");
        Serial.print("[HTTP] POST...\n");
        // start connection and send HTTP header
        int httpCode = http.POST("");

        // httpCode will be negative on error
        if (httpCode > 0) {
          // HTTP header has been send and Server response header has been handled
          Serial.printf("[HTTP] POST... code: %d\n", httpCode);

          // file found at server
          if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_MOVED_PERMANENTLY) {
            String payload = http.getString();
            Serial.println(payload);
          }
        } else {
          Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
        }

        http.end();
      } else {
        Serial.println("[HTTP] Unable to connect");
      }
      delay(1000);
    }
    else {
      Serial.println("Not pressed");
    }
  }

  delay(100);
}