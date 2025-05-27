#define redpin 10
#define bluepin 9
#define greenpin 11

int incoming = 0;


void setup() {
  pinMode(redpin, OUTPUT);
  pinMode(bluepin, OUTPUT);
  pinMode(greenpin, OUTPUT);

  Serial.begin(15000);
}

void loop() {

  if (Serial.available()){
    String input = Serial.readStringUntil('\n');
    int firstcomma = input.indexOf(',');
    int secondcomma = input .indexOf(',', firstcomma + 1);

    if (firstcomma > 0 && secondcomma > firstcomma){
      int R = input.substring(0, firstcomma).toInt();
      int G = input.substring(firstcomma + 1, secondcomma).toInt();
      int B = input.substring(secondcomma + 1).toInt();

      analogWrite(redpin, R);
      analogWrite(greenpin, G);
      analogWrite(bluepin, B);
    }

  }
  delay(10);
}
