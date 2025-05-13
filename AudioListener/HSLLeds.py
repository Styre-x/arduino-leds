import serial
import time
import atexit
import sounddevice as sd
import numpy as np
import tkinter as tk

arduino = serial.Serial("/dev/ttyACM0", 20000, timeout=1)

brightness = 1 # float 0-1 for percent brightness of the LEDs. Not linear when changed, different setups have differentlower ranges.
# setting it too low can lead to non reactive lights. Higher brightness = more colors.

attack_rate = 0.9    # how quickly it jumps up 0-1
decay_rate  = 0.6   # how slowly it falls back 1-0

sampleRate = 44100 #bitrate for the sample. 
duration = 0.025 # seconds to sample from - lower = quick response/higher = smoother response
# I found a value of 0.025 was good for quicker energetic music but was a bit flashy.
# A value of 0.1 is where I like to keep it.
# Values below 0.025 lead to heavy flashing due to little time to average over, but have fun :)

All = [0,20000]
High = [4500, 20000]    #[4000, 20000]raw freq  #[6000, 20000] mostly white with jumps
Mids = [300, 4500]      #[500, 4000]            #[650, 6500]
Lows = [0, 300]         #[0, 500]               #[0, 1000]
MidsHigh = [0, 10000]
nothing = [0, 10]

AudioRanges = {
    "Lum": All,
    "Sat": Lows,
    "Hue": All
}

Maxes = {
    "Lum": 1,
    "Sat": 1,
    "Hue": 1
}

freqs = np.fft.rfftfreq(int(sampleRate*duration) * 2, 1/sampleRate)

class normalizer():
    def __init__(self):
        self.max = 1
        self.min = 0

    def clear(self):
        self.min = 0
        self.max = 1

    def normalize(self, input, delta = 1):
        if input > self.max:
            self.max = input
        elif input < self.min:
            self.min = input
        return np.clip(delta * (input - self.min) / (self.max - self.min), 0, delta)

class parser():
    def __init__(self, parseType):
        self.parseType = parseType
        self.env = 0
        self.normalizer = normalizer()
        self.maxNorm = Maxes[parseType]

    def getPWM(self, audio):

        fft = np.abs(np.fft.rfft(audio))

        freq = fft[(freqs >= AudioRanges[self.parseType][0]) & (freqs <= AudioRanges[self.parseType][1])]

        raw = np.sum(freq)

        if raw > self.env:
            self.env += attack_rate * (raw - self.env)
        else:
            self.env += decay_rate  * (raw - self.env)

        normalized = self.normalizer.normalize(self.env, self.maxNorm)

        normalized = (normalized + 0.5) % 1

        return normalized

def sendRGB(R, G, B):
    R = int(R)
    G = int(G)
    B = int(B)
    data = f"{R},{G},{B}\n"
    arduino.write(data.encode())

def hueRGB(p, q, t):
    t = np.clip(t, 0, 1)
    if t < 1/6: return p + (q-p)*6*t
    if t < 1/2: return q
    if t < 2/3: return p + (q-p)*(2/3-t)*6
    return p

def sendHSL(Hue, Sat, Lum):
    if Sat <= 0.1:
        Sat = 0.1
    q = Lum * (1 + Sat) if Lum < 0.5 else Lum + Sat - Lum * Sat
    p = 2 * Lum - q
    r = hueRGB(p, q, Hue + 1/3)*255
    g = hueRGB(p, q, Hue)*255
    b = hueRGB(p, q, Hue - 1/3)*255

    sendRGB(r,g,b)

#TODO: this is bad - a mic can be an input
stream = sd.InputStream(
    channels=2,
    samplerate=sampleRate,
    blocksize=int(sampleRate * duration)
)
stream.start()

Hue = parser("Hue")
Sat = parser("Sat")
Lum = parser("Lum")

try:
   while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()
        #Hue.getPWM(audio)
        sendHSL(Hue.getPWM(audio), Sat.getPWM(audio), 0.5) #Lum.getPWM(audio)
        #sendRGB(RLed.getPWM(audio), GLed.getPWM(audio), BLed.getPWM(audio))
except KeyboardInterrupt:
    stream.stop()
    stream.close()
    sendRGB(0,0,0) # turn off the lights when the program stops.
finally:
    print("\nexiting")
stream.stop()
stream.close()
sendRGB(0,0,0)
