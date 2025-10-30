import serial
import sounddevice as sd
import numpy as np
import argparse
import sys

brightness = 1 # float 0-1 for percent brightness of the LEDs. Not linear when changed, different setups have differentlower ranges.
# setting it too low can lead to non reactive lights. Higher brightness = more colors.
minBrightness = 0

attack_rate = 1    # how quickly it jumps up 0-1
decay_rate  = 1.2   # how slowly it falls back 1-0

resting = 0.18 # resting color H in HSV. 0-1

sampleRate = 44100 #bitrate for the sample. 
duration = 0.025 # seconds to sample from - lower = quick response/higher = smoother response
# I found a value of 0.025 was good for quicker energetic music but was a bit flashy.
# Changing this can lead to an entire re-calibration of the parser! Changing it by itself is not great without self-normalization and printing the max value to compensate if self-normalization is not wanted.
# Values below 0.025 lead to heavy flashing due to little time to average over, but have fun :)
# changing this with selfNormalized set to False will require a re-normalize

selfNormalize = True # Should it adapt to your music?
# Set to true and it will automatically set the max for your music.
# I did not like the reset after a restart so I added this.
selfMax = 17000 # This should be a good amount above the max given by the normalizer through print(self.max) in input > self.max
# too high and it will never turn green, too low and it will always be white. I do not like green so it is quite high!
# recalibrate when changing variables such as duration or bitrate. Not recalibrating can lead to an inactive light

silence = 0.05 # how low does it need to be to be fully white? set to 0 for darkness when quiet.

All = [0,20000]
High = [4000, 20000]    #[4000, 20000]raw freq  #[6000, 20000] mostly white with jumps
Mids = [300, 5000]      #[500, 4000]            #[650, 6500]
Lows = [0, 550]         #[0, 500]               #[0, 1000]

rgbMax = [255,255,255]

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--brightness", type=float, help="set light brightness (0-1)")
parser.add_argument("-l", "--low", type=float, help="set min brightness (0-1) - relative to brightness: 0.5 will be 0.1 with a brightness of 0.2")
parser.add_argument("-n", "--normal", help="set self-normalization to false", action="store_true")
parser.add_argument("-rgb", "--rgb", type=str, help="set rgb max to given tuple r,g,b. Range 0-255")
parser.add_argument("arduino", type=str)

args = parser.parse_args()

arduino = serial.Serial(args.arduino, 200000, timeout=1)

if args.brightness is not None:
    brightness = args.brightness

if args.low is not None:
    minBrightness = args.low * brightness

if args.rgb is not None:
    rgbMax = list(map(int, args.rgb.split(",")))

#if args.normal:
#    selfNormalize = False

freqs = np.fft.rfftfreq(int(sampleRate*duration) * 2, 1/sampleRate)

def downsample(arr, target_size, mulval):
    # Trim array to make it evenly divisible
    trim_size = (len(arr) // target_size) * target_size
    trimmed = np.array([item * mulval for item in arr[:trim_size]])
    return list(map(int, np.clip(trimmed.reshape(target_size, -1).mean(axis=1), 0, 256)))

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
        self.lowenv = 0
        self.highenv = 0
        self.rotator = 0.18
        self.normalizer = normalizer()

    def freqToNote(self, freq):
        if freq <= 0:
            return 0
        note = 69 + 12 * np.log2(freq/ 440.0)
        return round(note)

    def getPWM(self, audio):
# trying to change to notes rather than frequency
        fft = np.abs(np.fft.rfft(audio))
        lowFreq = fft[(freqs >= Lows[0]) & (freqs <= Lows[1])]
        midFreq = fft[(freqs >= Mids[0]) & (freqs <= Mids[1])]
        highFreq = fft[(freqs >= High[0]) & (freqs <= High[1])]

        # 28, 235, 800 different frequency items in the list
        # Uncomment for visualizer (bad)
        # visualLow = downsample(lowFreq, 6, 2)
        # visualMid = downsample(midFreq, 8, 6)
        # visualHigh = downsample(highFreq, 6, 10)
        # otherflag = " ".join(map(str, visualLow)) + " ".join(map(str, visualMid)) + " ".join(map(str, visualHigh)) # was 0 to support flagging for the addressable strip
        #print(visualLow, visualMid, visualHigh)
        
        # basically, it takes all frequencies and averages - terrible signal processing - it only reacts to volume changes.
        # change how much each is multiplied by to change how reactive each frequency is. relative is important! - 201/200/200 will look the same as 2.01/2/2
        # changing to be too far away from eachother, 1/0.1/1 will be flashy due to spikes in one frequency
        # I found these pleasant for the music I listen to - different music is a LOT different in what it spikes and what should be emphasised.
        # rawL = np.sum(lowFreq) * 1.5
        # rawM = np.sum(midFreq) * 1
        # rawH = np.sum(highFreq) * 1.5
        # raw = rawL + rawM + rawH

        rawL = np.sum(lowFreq) * 1.5
        rawM = np.sum(midFreq) * 1
        rawH = np.sum(highFreq) * 1.5
        raw = rawL + rawM + rawH
        otherflag = 1
        if raw > self.env:
            if attack_rate * (rawL - self.lowenv) > 600:
                otherflag = 1
            elif attack_rate * (rawH - self.highenv) > 550:
                otherflag = 1
            self.env += attack_rate * (raw - self.env)
            self.highenv += attack_rate * (rawH - self.highenv)
            self.lowenv += attack_rate * (rawL - self.lowenv)
        else:
            self.env += decay_rate  * (raw - self.env)

        normalized = self.normalizer.normalize(self.env, 1)

        normalized = (normalized + self.rotator) % 1 # sitting at 0.5 value allows for the 0 state to be white.
#        if normalized < 0.0001:
#            normalized = resting
        
        # rotate the HSV wheel to make it more interesting.
        self.rotator += 0.001
        if self.rotator >= 1:
            self.rotator = 0

        return normalized, otherflag

def sendRGB(R, G, B, flag):
    if minBrightness != 0:
        R = minBrightness + (1 - minBrightness) * R
        B = minBrightness + (1 - minBrightness) * B
        G = minBrightness + (1 - minBrightness) * G
    if rgbMax[0] == 0:
        G = (G+R)/2
        B = (B+R)/2
    if rgbMax[1] == 0:
        R = (R+G)/2
        B = (B+G)/2
    if rgbMax[2] == 0:
        R = (R+B)/2
        G = (G+B)/2
    R = int(R*rgbMax[0])
    G = int(G*rgbMax[1])
    B = int(B*rgbMax[2])
    data = f"{R},{G},{B},{flag}\n"
    arduino.write(data.encode())

def sendHSV(h, s, v, flag):
    if s == 0.0:
        return sendRGB(v, v, v, flag)
    i = int(h * 6.)
    f = (h * 6) - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i %= 6
    if i == 0:
        return sendRGB(v, t, p, flag)
    if i == 1:
        return sendRGB(q, v, p, flag)
    if i == 2:
        return sendRGB(p, v, t, flag)
    if i == 3:
        return sendRGB(p, q, v, flag)
    if i == 4:
        return sendRGB(t, p, v, flag)
    if i == 5:
        return sendRGB(v, p, q, flag)

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
        h, flag = Hue.getPWM(audio)
        sendHSV(h,1,brightness, flag)
except KeyboardInterrupt:
    stream.stop()
    stream.close()
    for i in range(250): # turn off the lights when the program stops.
        sendRGB(0,0,0, 0)
finally:
    print("\nexiting")
    stream.stop()
    stream.close()
    sendRGB(0,0,0, 0)
