#define redpin 10
#define bluepin 9


// void setRGB(int R, int G, int B){
//   digitalWrite(redport, LOW);
//   digitalWrite(blueport, LOW);
//   for (int i = 0; i == 1000; i++){
//     if (R == i){
//       digitalWrite(redport, HIGH);
//     }
//     if (G == i){
      
//     }
//     if (B == i){
//       digitalWrite(blueport, HIGH);
//     }
//     delay(1);
//   }
// }
int incoming = 0;


void setup() {
  // put your setup code here, to run once:
  pinMode(10, OUTPUT);
  pinMode(9, OUTPUT);

  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  //setRGB(10, 100, 10);
  //analogWrite(redpin, 200);
  //analogWrite(bluepin,255);

  if (Serial.available()){
    String input = Serial.readStringUntil('\n');
    int firstcomma = input.indexOf(',');
    int secondcomma = input .indexOf(',', firstcomma + 1);

    if (firstcomma > 0 && secondcomma > firstcomma){
      int R = input.substring(0, firstcomma).toInt();
      int G = input.substring(firstcomma + 1, secondcomma).toInt();
      int B = input.substring(secondcomma + 1).toInt();

      analogWrite(redpin, R);
      analogWrite(bluepin, B);
    }

  }
  delay(10);
}
