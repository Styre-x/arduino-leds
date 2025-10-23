#include <FastLED.h>
//OLD STRIP
#define redpin 10
#define bluepin 11
#define greenpin 9

#define LED_PIN 3
#define NUM_LEDS 89
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
CRGB leds[NUM_LEDS];
int values[NUM_LEDS * 3];
int idx = 0;

void setup() {
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  Serial.begin(20000);
  pinMode(redpin, OUTPUT);
  pinMode(bluepin, OUTPUT);
  pinMode(greenpin, OUTPUT);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    idx = 0;

    char *token = strtok((char*)input.c_str(), ",");
    while (token != NULL && idx < NUM_LEDS * 3) {
      values[idx++] = atoi(token);
      token = strtok(NULL, ",");
    }

    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i].setRGB(values[i * 3], values[i * 3 + 1], values[i * 3 + 2]);
    }
    // OLD STRIP
    analogWrite(redpin, values[0]);
    analogWrite(greenpin, values[1]);
    analogWrite(bluepin, values[2]);

    FastLED.show();
  }
}
