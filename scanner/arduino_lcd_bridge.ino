#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 20, 4);

#define BUZZER_PIN 8

#define BUZZER_ON  LOW
#define BUZZER_OFF HIGH

String inputLine = "";
unsigned long lastMessageAt = 0;

void buzzerMute() {
  digitalWrite(BUZZER_PIN, BUZZER_OFF);
}

void beep(int duration) {
  digitalWrite(BUZZER_PIN, BUZZER_ON);  
  delay(duration);
  digitalWrite(BUZZER_PIN, BUZZER_OFF); 
  delay(60);
}

void beepSuccess() {
  beep(200);
}

void beepFailure() {
  for (int i = 0; i < 4; i++) {
    beep(100);
  }
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
    beepSuccess();
  } else {
    beepFailure();
  }
}

void setup() {
  Serial.begin(9600);
  
  pinMode(BUZZER_PIN, OUTPUT);
  buzzerMute();

  inputLine.reserve(128);
  
  delay(100);
  lcd.init();
  lcd.backlight(); 
  lcd.clear();
  
  showDefaultScreen();
  beepSuccess(); 
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      showPayload(inputLine);
      inputLine = ""; 
    } else if (c != '\r') {
      inputLine += c;
    }
  }

  if (lastMessageAt > 0 && millis() - lastMessageAt > 5000) {
    showDefaultScreen();
    lastMessageAt = 0;
  }
}