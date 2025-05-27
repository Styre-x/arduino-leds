import serial
import time
import atexit
import sounddevice as sd
import numpy as np
import tkinter as tk

arduino = serial.Serial("/dev/ttyACM0", 15000, timeout=1)

brightness = 1 # float 0-1 for percent brightness of the LEDs. Not linear when changed, different setups have differentlower ranges.
# setting it too low can lead to non reactive lights. Higher brightness = more colors.

attack_rate = 1    # how quickly it jumps up 0-1
decay_rate  = 0.8   # how slowly it falls back 1-0

sampleRate = 44100 #bitrate for the sample. 
duration = 0.025 # seconds to sample from - lower = quick response/higher = smoother response
# I found a value of 0.025 was good for quicker energetic music but was a bit flashy.
# A value of 0.1 is where I like to keep it.
# Values below 0.025 lead to heavy flashing due to little time to average over, but have fun :)

All = [0,20000]
High = [4000, 20000]    #[4000, 20000]raw freq  #[6000, 20000] mostly white with jumps
Mids = [300, 5000]      #[500, 4000]            #[650, 6500]
Lows = [0, 550]         #[0, 500]               #[0, 1000]
MidsHigh = [0, 4500]
nothing = [0, 10]

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
        self.maxNorm = 1

    def getPWM(self, audio):

        fft = np.abs(np.fft.rfft(audio))
        lowFreq = fft[(freqs >= Lows[0]) & (freqs <= Lows[1])]
        midFreq = fft[(freqs >= Mids[0]) & (freqs <= Mids[1])]
        highFreq = fft[(freqs >= High[0]) & (freqs <= High[1])]
        
        # basically, it takes all frequencies and averages - terrible signal processing - it only reacts to volume changes.
        # change how much each is multiplied by to change how reactive each frequency is. relative is important! - 201/200/200 will look the same as 2.01/2/2
        # changing to be too far away from eachother, 1/0.1/1 will be flashy due to spikes in one frequency
        # I found these pleasant for the music I listen to - different music is a LOT different in what it spikes and what should be emphasised.
        rawL = np.sum(lowFreq) * 1.2
        rawM = np.sum(midFreq) * 0.75
        rawH = np.sum(highFreq) * 1.2
        raw = rawL + rawM + rawH

        if raw > self.env:
            self.env += attack_rate * (raw - self.env)
        else:
            self.env += decay_rate  * (raw - self.env)

        normalized = self.normalizer.normalize(self.env, self.maxNorm)

        normalized = (normalized + 0.5) % 1 # sitting at 0.5 value allows for the 0 state to be white.

        return normalized

def sendRGB(R, G, B):
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
Sat = parser("Sat")
Lum = parser("Lum")

try:
   while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()
        sendHSV(Hue.getPWM(audio), 1,1) # lumination and value are set constant to make it brighter.
except KeyboardInterrupt:
    stream.stop()
    stream.close()
    sendRGB(0,0,0) # turn off the lights when the program stops.
finally:
    print("\nexiting")
stream.stop()
stream.close()
sendRGB(0,0,0)
