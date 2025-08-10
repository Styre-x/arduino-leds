import serial
import time
arduino = serial.Serial("/dev/ttyACM0", 20000, timeout=1)
while True:
    arduino.write(f"{int(255)},{int(255)},{int(255)}\n".encode())
    time.sleep(0.025)
