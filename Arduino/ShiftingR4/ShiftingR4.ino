#include <FastLED.h>
//OLD STRIP
#define redpin 10
#define bluepin 11
#define greenpin 9

#define LED_PIN 4
#define NUM_LEDS 90 // should be even
#define LED_TYPE WS2812B
#define COLOR_ORDER BRG

typedef struct Node node;

struct Node {
    unsigned char *r;
    unsigned char *g;
    unsigned char *b;
    node *next;
    node *last;
};

typedef struct List {
    node *head;
} list;

CRGB leds[NUM_LEDS];
list* values;
node* last;
node* current;
int length = 0;
int idx = 0;

list* create_list(){
    list* first = (list*)malloc(sizeof(node*));
    first->head = NULL;
    return first;
};

void add_to_list(list* ll, unsigned char r, unsigned char g, unsigned char b){
    node* first = (node*)malloc(sizeof(node));
    if (ll->head != NULL){
      first->next = ll->head;
      ll->head->last = first;
    }else{
      first->next = NULL;
      first->last = NULL;
    }
    first->r = (unsigned char*)malloc(sizeof(unsigned char));
    first->g = (unsigned char*)malloc(sizeof(unsigned char));
    first->b = (unsigned char*)malloc(sizeof(unsigned char));

    *first->r = r;
    *first->g = g;
    *first->b = b;

    ll->head = first;
};

void setup() {
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  //FastLED.setBrightness(20);
  Serial.begin(200000);
  pinMode(redpin, OUTPUT);
  pinMode(bluepin, OUTPUT);
  pinMode(greenpin, OUTPUT);

  values = create_list();
}

void loop() {
  if (Serial.available()) {
    //delay(100);
    String input = Serial.readStringUntil('\n');
    int firstcomma = input.indexOf(',');
    int secondcomma = input .indexOf(',', firstcomma + 1);
    int thirdcomma = input.indexOf(',', secondcomma+1);

    if (firstcomma > 0 && secondcomma > firstcomma){
      int R = input.substring(0, firstcomma).toInt();
      int G = input.substring(firstcomma + 1, secondcomma).toInt();
      int B = input.substring(secondcomma + 1, thirdcomma).toInt();

      int flag = input.substring(thirdcomma+1).toInt();

      analogWrite(redpin, R);
      analogWrite(greenpin, G);
      analogWrite(bluepin, B);

      if (flag == 1){
        add_to_list(values, (unsigned char)R, (unsigned char)G, (unsigned char)B);
      }else{
        add_to_list(values, 0, 0, 0);
      }
      
      if (length == NUM_LEDS/4 + 1){
        node* newlast = last->last;
        free(last->r);
        free(last->g);
        free(last->b);
        free(last);
        last = newlast;
        last->next = NULL;
      }else{
        if (length == 0){
          last = values->head;
        }
        length++;
      }

      current = last;
      int i = 0;
      while (current != NULL && i < NUM_LEDS/2){
        leds[i].setRGB(*current->r, *current->g, *current->b);
        leds[NUM_LEDS - i-1].setRGB(*current->r, *current->g, *current->b);
        i++;
        if (i%2 == 0){
          current = current->last;
        }
      }
    }

    FastLED.show();
  }
}
