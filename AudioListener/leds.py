import sounddevice as sd
import numpy as np
import serial
import time
import atexit

arduino = serial.Serial("/dev/ttyACM0", 9600, timeout=1)

brightness = 1 # float 0-1 for percent brightness of the LEDs. Not linear when changed, different setups have differentlower ranges.
# setting it too low can lead to non reactive lights. Higher brightness = more colors.

attack_rate = 0.8    # how quickly it jumps up (0–1)
decay_rate  = 0.2   # how slowly it falls back

sampleRate = 44100 #bitrate for the sample. 
duration = 0.01 # seconds to sample from - lower = quick response/higher = smoother response
# I found a value of 0.025 was good for quicker energetic music but was a bit flashy.
# A value of 0.1 is where I like to keep it.
# Values below 0.025 lead to heavy flashing due to little time to average over, but have fun :)

AudioRanges = {
    "Red": [0, 550],
    "Green": [6000, 20000],
    "Blue": [550, 6000]
}

freqs = np.fft.rfftfreq(int(sampleRate*duration) * 2, 1/sampleRate)

class normalizer():
    def __init__(self):
        self.max = 1
        self.min = 0

    def normalize(self, input, delta = 1):
        if input > self.max:
            self.max = input
        elif input < self.min:
            self.min = input
        return np.clip(delta * (input - self.min) / (self.max - self.min), 0, delta)

class light():
    def __init__(self, ledColor):
        self.ledColor = ledColor
        self.env = 0
        self.normalizer = normalizer()

    def getPWM(self, audio):
        raw = self.getRange(audio, AudioRanges[self.ledColor][0], AudioRanges[self.ledColor][0])
        if raw > self.env:
            self.env += attack_rate * (raw - self.env)
        else:
            self.env += decay_rate  * (raw - self.env)
        return self.normalizer.normalize(self.env, 255) * brightness

    def getRange(self, audio, lowRange, HighRange):
        fft = np.abs(np.fft.rfft(audio))

        freq = fft[(freqs >= lowRange) & (freqs <= HighRange)]

        total = np.sum(freq)

        return total 

    

def sendRGB(R, G, B):
    R = int(R)
    G = int(G)
    B = int(B)
    data = f"{R},{G},{B}\n"
    arduino.write(data.encode())

stream = sd.InputStream(
    channels=2,
    samplerate=sampleRate,
    blocksize=int(sampleRate * duration)
)
stream.start()

RLed = light("Red")
GLed = light("Green")
BLed = light("Blue")

try:
    while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()

        sendRGB(RLed.getPWM(audio), GLed.getPWM(audio), BLed.getPWM(audio))
except KeyboardInterrupt:
    print("\nexiting")
finally:
    stream.stop()
    stream.close()
    sendRGB(0,0,0) # turn off the lights when the program stops. 
