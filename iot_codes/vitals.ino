#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <LiquidCrystal_I2C.h>

MAX30105 particleSensor;
LiquidCrystal_I2C lcd(0x27, 16, 2);

#define BUFFER_SIZE 100 
uint32_t redBuffer[BUFFER_SIZE];
uint32_t irBuffer[BUFFER_SIZE];

#define MAX_VALID_BPM 180
#define MIN_VALID_BPM 40
#define MAX_VALID_SPO2 100
#define MIN_VALID_SPO2 85

float bpmSum = 0;
int bpmCount = 0;
float spo2Sum = 0;
int spo2Count = 0;
float lastValidBPM = -1;
float lastValidSpO2 = -1;

void setup() {
  Serial.begin(9600);
  delay(1000);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Initializing...");

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    lcd.setCursor(0, 1);
    lcd.print("Sensor not found");
    while (1);
  }

  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x0A);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Place your finger");
  lcd.setCursor(0, 1);
  lcd.print("on the sensor...");
}

void loop() {
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();

  static int i = 0;
  static float bpm = -1;

  if (irValue < 10000) {
    lcd.setCursor(0, 0);
    lcd.print("Waiting for     ");
    lcd.setCursor(0, 1);
    lcd.print("finger...       ");
    Serial.println("Place finger on sensor...");
    delay(500);
    return;
  }

  redBuffer[i] = redValue;
  irBuffer[i] = irValue;
  i++;

  // Detect heartbeat
  if (checkForBeat(irValue)) {
    static long lastBeat = 0;
    long now = millis();
    long delta = now - lastBeat;
    lastBeat = now;

    float currentBPM = 60.0 / (delta / 1000.0);

    if (currentBPM > MIN_VALID_BPM && currentBPM < MAX_VALID_BPM) {
      bpm = currentBPM;
      bpmSum += bpm;
      bpmCount++;
      lastValidBPM = bpm;
    }
  }

  if (i >= BUFFER_SIZE) {
    float meanRed = 0, meanIR = 0, stdRed = 0, stdIR = 0;

    for (int j = 0; j < BUFFER_SIZE; j++) {
      meanRed += redBuffer[j];
      meanIR += irBuffer[j];
    }
    meanRed /= BUFFER_SIZE;
    meanIR /= BUFFER_SIZE;

    for (int j = 0; j < BUFFER_SIZE; j++) {
      stdRed += pow(redBuffer[j] - meanRed, 2);
      stdIR += pow(irBuffer[j] - meanIR, 2);
    }
    stdRed = sqrt(stdRed / BUFFER_SIZE);
    stdIR = sqrt(stdIR / BUFFER_SIZE);

    float ratio = (stdRed / meanRed) / (stdIR / meanIR);
    float spo2 = 110.0 - 25.0 * ratio;
    spo2 = constrain(spo2, 0, 100);

    if (spo2 >= MIN_VALID_SPO2 && spo2 <= MAX_VALID_SPO2) {
      lastValidSpO2 = spo2;
      spo2Sum += spo2;
      spo2Count++;
    }

    float avgBPM = (bpmCount > 0) ? bpmSum / bpmCount : lastValidBPM;

    Serial.print("BPM: ");
    Serial.print(avgBPM, 1);
    Serial.print(" | SpO2: ");
    Serial.print(lastValidSpO2, 1);
    Serial.print("% | IR: ");
    Serial.println(irValue);

    Serial.print("<DATA,");
    Serial.print(avgBPM, 1);
    Serial.print(",");
    Serial.print(lastValidSpO2, 1);
    Serial.println(">");

    lcd.setCursor(0, 0);
    lcd.print("BPM: ");
    if (avgBPM > 0)
      lcd.print((int)avgBPM);
    else
      lcd.print("--");
    lcd.print(" SpO2:");
    lcd.print((int)lastValidSpO2);
    lcd.print("%");

    lcd.setCursor(0, 1);
    lcd.print("IR: ");
    lcd.print(irValue);
    lcd.print("     ");

    i = 0;

    // Reset BPM sum only if bpmCount > 0
    if (bpmCount > 0) {
      bpmSum = 0;
      bpmCount = 0;
    }
  }

  delay(20);
}
