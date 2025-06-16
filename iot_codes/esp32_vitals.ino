#include <WiFi.h>
#include <HTTPClient.h>

// WiFi Credentials
const char* ssid = "NV-2.4G";
const char* password = " ";

// ThingSpeak Settings
const char* server = "https://api.thingspeak.com/update";
const char* apiKey = " ";

// Serial2 (UART) pins for communication with Arduino
#define RXD2 16  // Connect to Arduino's TX
#define TXD2 17  // Optional

// Timer to manage ThingSpeak interval
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 5000; // 15 seconds

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println(" connected!");
}

void setup() {
  Serial.begin(115200);                           // Monitor output
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);     // UART2
  connectToWiFi();
  Serial.println("ESP32 listening for data from Arduino...");
}

void loop() {
  static String input = "";

  while (Serial2.available()) {
    char c = Serial2.read();

    if (c == '<') {
      input = ""; // Start new message
    } else if (c == '>') {
      parseMessage(input);
      input = "";
    } else {
      input += c;
    }
  }
}

void parseMessage(String msg) {
  msg.trim();

  if (msg.startsWith("DATA")) {
    msg.remove(0, 5); // Remove "DATA,"
    float bpm = msg.substring(0, msg.indexOf(',')).toFloat();
    float spo2 = msg.substring(msg.indexOf(',') + 1).toFloat();

    Serial.print("Live → BPM: ");
    Serial.print(bpm);
    Serial.print(" | SpO2: ");
    Serial.print(spo2);
    Serial.println("%");

    // Only send valid values
    if (bpm > 0 && spo2 > 85) {
      sendToThingSpeak(bpm, spo2);
    } else {
      Serial.println("✗ Skipping invalid values...");
    }
  } else {
    Serial.print("Unknown data: ");
    Serial.println(msg);
  }
}

void sendToThingSpeak(float bpm, float spo2) {
  if ((millis() - lastSendTime) < sendInterval) return;

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("✗ WiFi disconnected. Reconnecting...");
    connectToWiFi();
    return;
  }

  HTTPClient http;
  String url = String(server) + "?api_key=" + apiKey +
               "&field1=" + String(bpm, 1) +
               "&field2=" + String(spo2, 1);

  Serial.println("Sending to ThingSpeak...");
  Serial.println("URL: " + url);  // Debug line

  http.begin(url);
  http.setTimeout(10000); // 10 seconds

  int httpCode = http.GET();

  if (httpCode > 0) {
    Serial.print("✓ Data sent to ThingSpeak. HTTP code: ");
    Serial.println(httpCode);
  } else {
    Serial.print("✗ Error sending data. HTTP code: ");
    Serial.println(httpCode);
  }

  http.end();
  lastSendTime = millis(); // Reset timer
}
