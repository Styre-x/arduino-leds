#define FASTLED_ALLOW_INTERRUPTS 0
#include <FastLED.h>

#define LED_PIN 3
#define NUM_LEDS 95
#define BRIGHTNESS  100
#define LED_TYPE    WS2811
#define COLOR_ORDER GRB
CRGB leds[NUM_LEDS];

#define UPDATES_PER_SECOND 10

void setup() {
  delay(3000);

  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.setBrightness(  BRIGHTNESS );

  Serial.begin(19200);
}

void loop() {
  // for (int i = 0; i == NUM_LEDS-1; i++){
  //   leds[i] = CRGB(0,0,0);
  // }
  // FastLED.show();
  // put your main code here, to run repeatedly:
  if (Serial.available()){
    String input = Serial.readStringUntil('\n');
    int firstcomma = input.indexOf(',');
    int secondcomma = input .indexOf(',', firstcomma + 1);

    if (firstcomma > 0 && secondcomma > firstcomma){
      int R = input.substring(0, firstcomma).toInt();
      int G = input.substring(firstcomma + 1, secondcomma).toInt();
      int B = input.substring(secondcomma + 1).toInt();
      if (R == 255 && G == 255 && B == 255){
        fill_solid(leds, NUM_LEDS, CRGB::Blue);
        FastLED.show();
      }else{
        for (int i = 0; i < NUM_LEDS; i++){
          leds[i] = CRGB(R,G,B);
          //FastLED.show();
        }
        FastLED.show();
      }
      
    }
  }
  FastLED.delay(1000 / UPDATES_PER_SECOND);
}
