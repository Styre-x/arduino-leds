import sounddevice as sd
import numpy as np
import serial
import time
import atexit

arduino = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
time.sleep(2)

brightness = 1 # float 0-1 for percent brightness of the LEDs. Not linear when changed, different setups have differentlower ranges.
# some transistors have a smallest possible pulse width, so setting it too low can lead to non reactive lights. 
sampleRate = 44100 #bitrate for the sample. 
duration = 0.1 # seconds to sample from - lower = quick response/higher = smoother response
# I found a value of 0.025 was good for quicker energetic music but was a bit flashy.
# A value of 0.1 is where I like to keep it.
# Values below 0.025 lead to heavy flashing due to little time to average over, but have fun :)

def getRange(audio, lowRange, HighRange):
    fft = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1/sampleRate)

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

try:
    while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()

        bass = getRange(audio, 0, 450)
        mid = getRange(audio, 500, 1200)
        #high = 3000 6000

        if bass < bassMin:
            bassMin = bass
        if bass > bassMax:
            bassMax = bass

        if mid < midMin:
            midMin = mid
        if mid > midMax:
            midMax = mid

        pwmR = int(normalize(bass, bassMin, bassMax) * brightness)
        pwmB = int(normalize(mid, bassMin, bassMax) * brightness)

        sendRGB(pwmR, 0, pwmB)
except KeyboardInterrupt:
    print("exiting")
finally:
    stream.stop()
    stream.close()
    sendRGB(0,0,0) # turn off the lights when the program stops. 