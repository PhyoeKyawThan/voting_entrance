#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 20, 4);

#define BUZZER_PIN 8

#define BUZZER_ON  LOW
#define BUZZER_OFF HIGH

String inputLine = "";
unsigned long lastMessageAt = 0;
unsigned long lastCharAt = 0;

#define INPUT_LINE_MAX 128
#define INCOMPLETE_TIMEOUT 200

enum BuzzerState { BUZZER_IDLE, BUZZER_ON, BUZZER_BETWEEN };
BuzzerState buzzerState = BUZZER_IDLE;
unsigned long buzzerStartTime = 0;
int buzzerBeepCount = 0;
int buzzerTotalBeeps = 0;
int buzzerOnDuration = 0;
int buzzerOffDuration = 0;

void updateBuzzer() {
  if (buzzerState == BUZZER_IDLE) return;

  if (buzzerState == BUZZER_ON && millis() - buzzerStartTime >= buzzerOnDuration) {
    digitalWrite(BUZZER_PIN, BUZZER_OFF);
    buzzerState = BUZZER_BETWEEN;
    buzzerStartTime = millis();
  } else if (buzzerState == BUZZER_BETWEEN && millis() - buzzerStartTime >= buzzerOffDuration) {
    buzzerBeepCount++;
    if (buzzerBeepCount >= buzzerTotalBeeps) {
      buzzerState = BUZZER_IDLE;
      digitalWrite(BUZZER_PIN, BUZZER_OFF);
    } else {
      digitalWrite(BUZZER_PIN, BUZZER_ON);
      buzzerState = BUZZER_ON;
      buzzerStartTime = millis();
    }
  }
}

void startBeep(int totalBeeps, int onDuration, int offDuration) {
  buzzerTotalBeeps = totalBeeps;
  buzzerOnDuration = onDuration;
  buzzerOffDuration = offDuration;
  buzzerBeepCount = 0;
  buzzerState = BUZZER_ON;
  buzzerStartTime = millis();
  digitalWrite(BUZZER_PIN, BUZZER_ON);
}

void showDefaultScreen() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Secure Voting System");
  lcd.setCursor(0, 1);
  lcd.print("Waiting for scan...");
}

void showPayload(String payload) {
  int nameIndex = payload.indexOf("\"name\":\"");
  int statusIndex = payload.indexOf("\"status\":\"");
  int messageIndex = payload.indexOf("\"message\":\"");

  String name = "Unknown";
  String status = "";
  String message = "";

  if (nameIndex >= 0) {
    int start = nameIndex + 8;
    int end = payload.indexOf('"', start);
    if (end > start) name = payload.substring(start, end);
  }

  if (statusIndex >= 0) {
    int start = statusIndex + 10;
    int end = payload.indexOf('"', start);
    if (end > start) status = payload.substring(start, end);
  }

  if (messageIndex >= 0) {
    int start = messageIndex + 11;
    int end = payload.indexOf('"', start);
    if (end > start) message = payload.substring(start, end);
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(status == "SUCCESS" ? "ENTERING" : "ENTRY FAILED");
  lcd.setCursor(0, 1);
  lcd.print(name.substring(0, 20));
  lcd.setCursor(0, 2);
  lcd.print(message.substring(0, 20));
  lcd.setCursor(0, 3);
  lcd.print("Status: " + status);
  
  lastMessageAt = millis();

  if (status == "SUCCESS") {
    startBeep(1, 200, 60);
  } else {
    startBeep(4, 100, 60);
  }
}

void setup() {
  Serial.begin(9600);
  
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, BUZZER_OFF);

  inputLine.reserve(128);
  
  delay(100);
  lcd.init();
  lcd.backlight(); 
  lcd.clear();
  
  showDefaultScreen();
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      showPayload(inputLine);
      inputLine = ""; 
      lastCharAt = 0;
    } else if (c != '\r') {
      inputLine += c;
      lastCharAt = millis();
    }
  }

  if (inputLine.length() > 0 && lastCharAt > 0 && millis() - lastCharAt > INCOMPLETE_TIMEOUT) {
    inputLine = "";
    lastCharAt = 0;
  }

  if (inputLine.length() > INPUT_LINE_MAX) {
    inputLine = "";
    lastCharAt = 0;
  }

  if (lastMessageAt > 0 && millis() - lastMessageAt > 5000) {
    inputLine = "";
    lastCharAt = 0;
    showDefaultScreen();
    lastMessageAt = 0;
  }

  updateBuzzer();
}
