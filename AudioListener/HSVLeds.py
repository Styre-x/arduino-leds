import serial
import time
import math
import atexit
import sounddevice as sd
import numpy as np
import tkinter as tk
import argparse

arduino = serial.Serial("/dev/ttyACM0", 20000, timeout=1)

brightness = 1 # float 0-1 for percent brightness of the LEDs. Not linear when changed, different setups have differentlower ranges.
# setting it too low can lead to non reactive lights. Higher brightness = more colors.
minBrightness = 0

attack_rate = 1    # how quickly it jumps up 0-1
decay_rate  = 0.9   # how slowly it falls back 1-0

sampleRate = 44100 #bitrate for the sample. 
duration = 0.025 # seconds to sample from - lower = quick response/higher = smoother response
# I found a value of 0.025 was good for quicker energetic music but was a bit flashy.
# A value of 0.1 is where I like to keep it.
# Values below 0.025 lead to heavy flashing due to little time to average over, but have fun :)
# changing this with selfNormalized set to False will require a re-normalize

selfNormalize = False # Should it adapt to your music?
# Set to true and it will automatically set the max for your music.
# I did not like the reset after a restart so I added this.
selfMax = 17000 # This should be a good amount above the max given by the normalizer through print(self.max) in input > self.max
# too high and it will never turn green, too low and it will always be white. I do not like green so it is quite high!
# recalibrate when changing variable such as frequency multiplication

All = [0,20000]
High = [4000, 20000]    #[4000, 20000]raw freq  #[6000, 20000] mostly white with jumps
Mids = [300, 5000]      #[500, 4000]            #[650, 6500]
Lows = [0, 550]         #[0, 500]               #[0, 1000]

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--brightness", type=float, help="set light brightness (0-1)")
parser.add_argument("-l", "--low", type=float, help="set min brightness (0-1)")

args = parser.parse_args()

if args.brightness is not None:
    brightness = args.brightness

if args.low is not None:
    minBrightness = args.low

freqs = np.fft.rfftfreq(int(sampleRate*duration) * 2, 1/sampleRate)

class normalizer():
    def __init__(self):
        if selfNormalize:
            self.max = 1
        else:
            self.max = selfMax

    def clear(self):
        if selfNormalize:
            self.max = 1
        else:
            self.max = selfMax

    def normalize(self, input, delta = 1):
        if selfNormalize:
            if input > self.max:
                self.max = input
                print(self.max) # here for debug
        base = np.clip(delta * (input - 0) / (self.max - 0), 0, delta)
        return base

class parser():
    def __init__(self, parseType):
        self.parseType = parseType
        self.env = 0
        self.normalizer = normalizer()

    def getPWM(self, audio):

        fft = np.abs(np.fft.rfft(audio))
        lowFreq = fft[(freqs >= Lows[0]) & (freqs <= Lows[1])]
        midFreq = fft[(freqs >= Mids[0]) & (freqs <= Mids[1])]
        highFreq = fft[(freqs >= High[0]) & (freqs <= High[1])]
        
        # basically, it takes all frequencies and averages - terrible signal processing - it only reacts to volume changes.
        # change how much each is multiplied by to change how reactive each frequency is. relative is important! - 201/200/200 will look the same as 2.01/2/2
        # changing to be too far away from eachother, 1/0.1/1 will be flashy due to spikes in one frequency
        # I found these pleasant for the music I listen to - different music is a LOT different in what it spikes and what should be emphasised.
        rawL = np.sum(lowFreq) * 1.5
        rawM = np.sum(midFreq) * 1
        rawH = np.sum(highFreq) * 1.5
        raw = rawL + rawM + rawH

        if raw > self.env:
            self.env += attack_rate * (raw - self.env)
        else:
            self.env += decay_rate  * (raw - self.env)

        normalized = self.normalizer.normalize(self.env, 1)

        normalized = (normalized + 0.5) % 1 # sitting at 0.5 value allows for the 0 state to be white.

        return normalized

def sendRGB(R, G, B):
    if minBrightness != 0:
        R = minBrightness + (1 - minBrightness) * R
        B = minBrightness + (1 - minBrightness) * B
        G = minBrightness + (1 - minBrightness) * G
    
    R = int(R*255)
    G = int(G*255)
    B = int(B*255)
    data = f"{R},{G},{B}\n"
    arduino.write(data.encode())

def sendHSV(h, s, v):
    if s == 0.0:
        return sendRGB(v, v, v)
    i = int(h * 6.)
    f = (h * 6) - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i %= 6
    if i == 0:
        return sendRGB(v, t, p)
    if i == 1:
        return sendRGB(q, v, p)
    if i == 2:
        return sendRGB(p, v, t)
    if i == 3:
        return sendRGB(p, q, v)
    if i == 4:
        return sendRGB(t, p, v)
    if i == 5:
        return sendRGB(v, p, q)

#TODO: this is bad - a mic can be an input
stream = sd.InputStream(
    channels=2,
    samplerate=sampleRate,
    blocksize=int(sampleRate * duration)
)
stream.start()

Hue = parser("Hue")
#Sat = parser("Sat")
#Lum = parser("Lum")

try:
   while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()
        sendHSV(Hue.getPWM(audio), 1,brightness) # lumination and value are set constant to make it brighter.
except KeyboardInterrupt:
    stream.stop()
    stream.close()
    sendRGB(0,0,0) # turn off the lights when the program stops.
finally:
    print("\nexiting")
stream.stop()
stream.close()
sendRGB(0,0,0)
