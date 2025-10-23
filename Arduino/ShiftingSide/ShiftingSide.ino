#include <FastLED.h>
//OLD STRIP
#define redpin 10
#define bluepin 11
#define greenpin 9

#define LED_PIN 4
#define NUM_LEDS 90 // should be even
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

typedef struct Node node;

struct Node {
    int *r;
    int *g;
    int *b;
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

int add_to_list(list* ll, int* r, int* g, int* b){
    node* first = (node*)malloc(sizeof(node));
    if (ll->head != NULL){
      first->next = ll->head;
      ll->head->last = first;
    }else{
      first->next = NULL;
      first->last = NULL;
    }
    first->r = (int*)malloc(sizeof(int));
    first->g = (int*)malloc(sizeof(int));
    first->b = (int*)malloc(sizeof(int));

    first->r = r;
    first->g = g;
    first->b = b;

    ll->head = first;
    return 0;
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

//String input = "25,25,25\n";

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
        add_to_list(values, R, G, B);
      }else{
        add_to_list(values, 0, 0, 0);
      }
      
      if (length == NUM_LEDS/2){
        node* newlast = last->last;
        free(last);
        last = newlast;
        last->next = NULL;
      }else{
        if (length == 0){
          last = values->head;
        }
        length++;
      }

      current = values->head;
      int i = 0;
      while (current != NULL && i < NUM_LEDS/2){
        // to make it change from the center, looks cool
        //leds[(NUM_LEDS/2) - i].setRGB(current->g, current->r, current->b);
        //leds[(NUM_LEDS/2) + i-1].setRGB(current->g, current->r, current->b);
        leds[i].setRGB(current->g, current->r, current->b);
        leds[NUM_LEDS - i-1].setRGB(current->g, current->r, current->b);
        i++;
        current = current->next;
      }
      if (i < NUM_LEDS/2){
        for (i = i; i < NUM_LEDS/2; i++){
          leds[i].setRGB(0, 0, 0);
          leds[NUM_LEDS - i-1].setRGB(0,0,0);
        }
      }
    }

    FastLED.show();
  }
}
