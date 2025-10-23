import serial
import sounddevice as sd
import numpy as np
import time

# ====== SETTINGS ======
arduino = serial.Serial("/dev/ttyACM0", 200000, timeout=1)
sampleRate = 44100
duration = 0.025
numBands = 60
numLEDs = 100
brightness = 0.15
decay = 0.8

# define segments: (start_index, end_index, bandstart, bandend, shift)
# for example, (0, 30, 0) means LEDs 0–29 show band 0
# you can repeat bands to mirror effects
segments = [
    (0,100,0,numBands),

    (0,25,0,numBands),
    (76, 85, 0,numBands),
    (86, 100, 0, numBands),
    (0, 25, 5, 30),
    (70, 85, 20, 40),
    (86, 100, 30, 60),
]

###legacy parser
All = [0,20000]
High = [4000, 20000]    #[4000, 20000]raw freq  #[6000, 20000] mostly white with jumps
Mids = [300, 5000]      #[500, 4000]            #[650, 6500]
Lows = [0, 550]         #[0, 500]               #[0, 1000]

attack_rate = 1    # how quickly it jumps up 0-1
decay_rate  = 0.9   # how slowly it falls back 1-0
selfMax = 7500
legacy = False

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

class normalizer():
    def normalize(self, input, delta = 1):
        base = np.clip(delta * (input - 0) / (selfMax - 0), 0, delta)
        return base
    
##legacy for old strip
class parser():
    def __init__(self, parseType):
        self.parseType = parseType
        self.env = 0
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
        
        # basically, it takes all frequencies and averages - terrible signal processing - it only reacts to volume changes.
        # change how much each is multiplied by to change how reactive each frequency is. relative is important! - 201/200/200 will look the same as 2.01/2/2
        # changing to be too far away from eachother, 1/0.1/1 will be flashy due to spikes in one frequency
        # I found these pleasant for the music I listen to - different music is a LOT different in what it spikes and what should be emphasised.
        rawL = np.sum(lowFreq) * 1.5
        rawM = np.sum(midFreq) * 1
        rawH = np.sum(highFreq) * 1.5
        raw = rawL + rawM + rawH
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

oldH = parser("Hue")
colors = [(0, 0, 0)] * numLEDs

drop_flash = 0
drop_decay = 0.9
drop_threshold = 1.3  # how big a spike we need (relative to moving average)

avg_bass = 0
smooth_bass = 0

try:
    while True:
        audio, _ = stream.read(int(sampleRate * duration))
        audio = audio.flatten()
        bands = computeBands(audio)

        #bass lightness
        fft = np.abs(np.fft.rfft(audio))
        lowFreq = fft[(freqs >= Lows[0]) & (freqs <= Lows[1])]
        bass_energy = np.sum(lowFreq)

        smooth_bass = 0.9 * smooth_bass + 0.1 * bass_energy

        if bass_energy > drop_threshold * smooth_bass:
            drop_flash = 3  # trigger full flash
        else:
            drop_flash = 1
        # drop_flash *= drop_decay

        # hue_val = Hue.getPWM(audio)
        # v = brightness + (drop_flash * 0.8)  # flash adds to brightness temporarily
        # v = min(v, 1.0)  # clamp

        # hue across spectrum
        band_hues = [i / numBands for i in range(numBands)]
        band_rgbs = [HSV_to_RGB(h, 1, bands[i] * brightness * drop_flash) for i, h in enumerate(band_hues)]

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
        if legacy:
            colors[0] = (HSV_to_RGB(oldH.getPWM(audio),1,1))
        else:
            colors[0] = (0,0,0)
        sendStrip(colors)

except KeyboardInterrupt:
    sendStrip([(0, 0, 0)] * numLEDs)
    stream.stop()
    print("Stopped.")

