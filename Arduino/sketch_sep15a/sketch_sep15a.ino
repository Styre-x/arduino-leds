#define FASTLED_ALLOW_INTERRUPTS 0
#include <FastLED.h>

#define LED_PIN 4
#define NUM_LEDS 95
#define BRIGHTNESS  100
#define LED_TYPE    WS2811
#define COLOR_ORDER GRB
CRGB leds[NUM_LEDS];

#define UPDATES_PER_SECOND 30

void setup() {
  delay(3000);
  Serial.begin(9600);
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.setBrightness(  BRIGHTNESS );
}

void loop() {
  // for (int i = 0; i == NUM_LEDS-1; i++){
  //   leds[i] = CRGB(0,0,0);
  // }
  // FastLED.show();
  // put your main code here, to run repeatedly:
  for (int i = 0; i < 88; i++){
    leds[i].setRGB(255, 255, 255);
    FastLED.show();
    delay(100);
    leds[i].setRGB(0, 0, 0);
    FastLED.show();
    Serial.println(i);
  }
}
