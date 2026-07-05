#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 20, 4);

String inputLine = "";
unsigned long lastMessageAt = 0;

void showDefaultScreen() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Smart Entrance Ready");
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
}

void setup() {
  Serial.begin(9600);
  
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
    } else if (c != '\r') {
      inputLine += c;
    }
  }

  if (lastMessageAt > 0 && millis() - lastMessageAt > 5000) {
    showDefaultScreen();
    lastMessageAt = 0;
  }
}