import sounddevice as sd
import numpy as np
import serial
import time
import atexit

arduino = serial.Serial("/dev/ttyACM0", 9600, timeout=1)

brightness = 0.5 # float 0-1 for percent brightness of the LEDs. Not linear when changed, different setups have differentlower ranges.
# setting it too low can lead to non reactive lights. Higher brightness = more colors.
sampleRate = 44100 #bitrate for the sample. 
duration = 0.025 # seconds to sample from - lower = quick response/higher = smoother response
# I found a value of 0.025 was good for quicker energetic music but was a bit flashy.
# A value of 0.1 is where I like to keep it.
# Values below 0.025 lead to heavy flashing due to little time to average over, but have fun :)

freqs = np.fft.rfftfreq(int(sampleRate*duration) * 2, 1/sampleRate)

def getRange(audio, lowRange, HighRange):
    fft = np.abs(np.fft.rfft(audio))

    bass = fft[(freqs >= lowRange) & (freqs <= HighRange)]

    totalBass = np.sum(bass)

    return totalBass

def normalize(val, min, max):
    return int(np.clip(255* (val - min) / (max - min), 0, 255))

stream = sd.InputStream(
    channels=2,
    samplerate=sampleRate,
    blocksize=int(sampleRate * duration)
)
stream.start()

def sendRGB(R, G, B):
    data = f"{R},{G},{B}\n"
    arduino.write(data.encode())

def onExit():
    stream.close()

atexit.register(onExit)

bassMin = 0
bassMax = 1
midMin = 0
midMax = 1
highMin = 0
highMax = 1

try:
    while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()
        # low 0-450
        # mid 450 - 1200
        # high 1200-6000
        bass = getRange(audio, 0, 2500)
        mid = getRange(audio, 500, 8000)
        high = getRange(audio, 3250, 20000)
        #print(getRange(audio, 500, 510))
        #high = 3000 6000

        if bass < bassMin:
            bassMin = bass
        if bass > bassMax:
            bassMax = bass

        if mid < midMin:
            midMin = mid
        if mid > midMax:
            midMax = mid
        if high < highMin:
            highMin = high
        if high > highMax:
            highMax = high

        pwmLow = int(normalize(bass, bassMin, bassMax) * brightness)
        pwmMid = int(normalize(mid, bassMin, bassMax) * brightness)
        pwmHigh = int(normalize(high, highMin, highMax) * brightness)
        # RGB
        # High: Red
        # Mid: Green
        # Low: Blue
        sendRGB(pwmLow, pwmMid, pwmHigh)
except KeyboardInterrupt:
    print("exiting")
finally:
    stream.stop()
    stream.close()
    sendRGB(0,0,0) # turn off the lights when the program stops. 
