import serial
import sounddevice as sd
import numpy as np

# ====== SETTINGS ======
arduino = serial.Serial("/dev/ttyACM0", 200000, timeout=1)
sampleRate = 44100
duration = 0.025
numBands = 15  # more = smoother but slower visually
numLEDs = 105
brightness = 1.0
decay = 0.85  # higher = slower falloff

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

try:
    while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()
        fft = np.abs(np.fft.rfft(audio))
        
        bands = []
        for i in range(numBands):
            low, high = band_edges[i], band_edges[i + 1]
            mask = (freqs >= low) & (freqs < high)
            value = np.sum(fft[mask])
            # exponential moving average for smoothing
            energy_levels[i] = max(value, energy_levels[i] * decay)
            bands.append(energy_levels[i])
        
        max_val = np.max(bands) or 1
        bands = [b / max_val for b in bands]

        # map each band to a hue from 0–1 across the spectrum
        colors = []
        leds_per_band = numLEDs // numBands
        for i, val in enumerate(bands):
            hue = i / numBands  # 0–1 hue across the strip
            rgb = HSV_to_RGB(hue, 1, val * brightness)
            colors.extend([rgb] * leds_per_band)

        # fill any remainder LEDs
        while len(colors) < numLEDs:
            colors.append(colors[-1])

        sendStrip(colors)
except KeyboardInterrupt:
    sendStrip([(0, 0, 0)] * numLEDs)
    print("Stopped.")

