import serial
import sounddevice as sd
import numpy as np
import time

# ====== SETTINGS ======
arduino = serial.Serial("/dev/ttyACM0", 200000, timeout=1)
sampleRate = 44100
duration = 0.025
numBands = 20
numLEDs = 100
brightness = 0.5
decay = 0.8

# define segments: (start_index, end_index, band_index)
# for example, (0, 30, 0) means LEDs 0–29 show band 0
# you can repeat bands to mirror effects
segments = [
    (0,100,0,20),
    (0, 25, 2, 7),
    (76, 85, 8, 13),
    (86, 100, 10, 20),
]

# ====== UTILS ======
def HSV_to_RGB(h, s, v):
    if s == 0.0:
        v *= 255
        return (int(v), int(v), int(v))
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    i %= 6
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    elif i == 5: r, g, b = v, p, q
    return (int(r*255), int(g*255), int(b*255))

def sendStrip(colors):
    flat = [str(v) for rgb in colors for v in rgb]
    data = ",".join(flat) + "\n"
    arduino.write(data.encode())

# ====== MAIN ======
stream = sd.InputStream(channels=1, samplerate=sampleRate, blocksize=int(sampleRate * duration))
stream.start()

freqs = np.fft.rfftfreq(int(sampleRate * duration), 1/sampleRate)
band_edges = np.logspace(np.log10(20), np.log10(20000), numBands + 1)
energy_levels = np.zeros(numBands)

def computeBands(audio):
    fft = np.abs(np.fft.rfft(audio))
    for i in range(numBands):
        low, high = band_edges[i], band_edges[i + 1]
        mask = (freqs >= low) & (freqs < high)
        value = np.sum(fft[mask])
        energy_levels[i] = max(value, energy_levels[i] * decay)
    norm = energy_levels / (np.max(energy_levels) or 1)
    return norm

try:
    while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()
        bands = computeBands(audio)

        # hue across spectrum
        band_hues = [i / numBands for i in range(numBands)]
        band_rgbs = [HSV_to_RGB(h, 1, bands[i] * brightness) for i, h in enumerate(band_hues)]

        # build strip from segment definitions
        colors = [(0, 0, 0)] * numLEDs
        for start, end, bandmin, bandmax in segments:
            bandmax = int(np.clip(bandmax, 0, numBands - 1))
            for i in range(start, min(end, numLEDs)):
                init = i - start
                curr = int((i-start)/(end - start) * (bandmax - bandmin) + bandmin)
                rgb = band_rgbs[curr]
                if (colors[i] == (0,0,0)):
                    colors[i] = rgb
                else:
                    r,g,b = colors[i]
                    r1,g1,b1 = rgb
                    colors[i] = (r+r1/2, g+g1/2, b+b1/2)

        sendStrip(colors)

except KeyboardInterrupt:
    sendStrip([(0, 0, 0)] * numLEDs)
    stream.stop()
    print("Stopped.")

