import serial
import time
import atexit
import sounddevice as sd
import numpy as np
import tkinter as tk

# ChatGPT re-wrote this to add a UI. I don't really like it but it works.

class Normalizer:
    def __init__(self):
        self.max = 1
        self.min = 0

    def clear(self):
        self.min = 0
        self.max = 1

    def normalize(self, value, scale=1):
        if value > self.max:
            self.max = value
        if value < self.min:
            self.min = value
        return np.clip((value - self.min) / (self.max - self.min) * scale, 0, scale)

class Light:
    def __init__(self, color, app):
        self.color = color
        self.app = app
        self.env = 0
        self.norm = Normalizer()

    def get_pwm(self, audio):
        low, high = self.app.audio_ranges[self.color]
        fft = np.abs(np.fft.rfft(audio))
        band = fft[(self.app.freqs >= low) & (self.app.freqs <= high)]
        raw = band.sum() + band.max() * self.app.peak_rate

        if raw > self.env:
            self.env += self.app.attack_rate * (raw - self.env)
        else:
            self.env += self.app.decay_rate * (raw - self.env)

        return self.norm.normalize(self.env, 255) * self.app.brightness

class LEDApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Arduino LEDs")

        # Top-level parameters
        self.brightness   = 1.0      # 0.0 - 1.0
        self.attack_rate  = 0.5      # normalized
        self.decay_rate   = 0.2      # normalized
        self.peak_rate    = 0.0      # multiplier
        self.sample_rate  = 44100    # Hz
        self.duration     = 0.025    # seconds (25 ms)

        # Audio ranges for RGB
        self.audio_ranges = {
            "Red":   (0, 300),
            "Green": (4500, 20000),
            "Blue":  (300, 4500),
        }
        self._recompute_freqs()

        # Hardware setup
        self.arduino = serial.Serial("/dev/ttyACM0", 19200, timeout=1)
        self.stream  = sd.InputStream(
            channels=2,
            samplerate=self.sample_rate,
            blocksize=int(self.sample_rate * self.duration)
        )
        self.stream.start()

        # Create lights
        self.R = Light("Red",   self)
        self.G = Light("Green", self)
        self.B = Light("Blue",  self)

        # GUI variables
        self.brightness_var   = tk.DoubleVar(value=self.brightness * 100)
        self.attack_var       = tk.DoubleVar(value=self.attack_rate * 100)
        self.decay_var        = tk.DoubleVar(value=self.decay_rate * 100)
        self.peak_var         = tk.DoubleVar(value=self.peak_rate * 100)
        self.sample_rate_var  = tk.StringVar(value=str(self.sample_rate))
        self.duration_var     = tk.StringVar(value=str(int(self.duration * 1000)))  # ms

        # Frequency band vars
        self.red_low_var      = tk.StringVar(value=str(self.audio_ranges["Red"][0]))
        self.red_high_var     = tk.StringVar(value=str(self.audio_ranges["Red"][1]))
        self.green_low_var    = tk.StringVar(value=str(self.audio_ranges["Green"][0]))
        self.green_high_var   = tk.StringVar(value=str(self.audio_ranges["Green"][1]))
        self.blue_low_var     = tk.StringVar(value=str(self.audio_ranges["Blue"][0]))
        self.blue_high_var    = tk.StringVar(value=str(self.audio_ranges["Blue"][1]))

        # validate integer inputs
        vcmd = (self.register(self._validate_int), '%P')

        # Traces and widgets
        self.brightness_var.trace_add("write", self.on_brightness_change)
        self.attack_var.trace_add("write", self.on_attack_change)
        self.decay_var.trace_add("write", self.on_decay_change)
        self.peak_var.trace_add("write", self.on_peak_change)
        self.sample_rate_var.trace_add("write", self.on_sample_rate_change)
        self.duration_var.trace_add("write", self.on_duration_change)

        for color in ["Red", "Green", "Blue"]:
            getattr(self, f"{color.lower()}_low_var").trace_add("write", \
                lambda *args, c=color: self.on_band_change(c))
            getattr(self, f"{color.lower()}_high_var").trace_add("write", \
                lambda *args, c=color: self.on_band_change(c))

        # Layout
        tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL,
                 label="Brightness %", variable=self.brightness_var).pack(pady=5)
        tk.Scale(self, from_=0, to=120, orient=tk.HORIZONTAL,
                 label="Attack %",     variable=self.attack_var).pack(pady=5)
        tk.Scale(self, from_=0, to=120, orient=tk.HORIZONTAL,
                 label="Decay %",      variable=self.decay_var).pack(pady=5)
        tk.Scale(self, from_=0, to=1000, orient=tk.HORIZONTAL,
                 label="Peak %",       variable=self.peak_var).pack(pady=5)

        tk.Label(self, text="Sample Rate (Hz)").pack()
        tk.Spinbox(self, from_=8000, to=96000, increment=1000,
                   textvariable=self.sample_rate_var,
                   validate='key', validatecommand=vcmd).pack(pady=5)

        tk.Label(self, text="Duration (ms)").pack()
        tk.Spinbox(self, from_=1, to=1000, increment=1,
                   textvariable=self.duration_var,
                   validate='key', validatecommand=vcmd).pack(pady=5)

        # Frequency band controls
        freq_frame = tk.LabelFrame(self, text="Frequency Bands (Hz)")
        freq_frame.pack(pady=5, fill="x")
        tk.Label(freq_frame, text="Color").grid(row=0, column=0)
        tk.Label(freq_frame, text="Low").grid(row=0, column=1)
        tk.Label(freq_frame, text="High").grid(row=0, column=2)
        for idx, color in enumerate(["Red", "Green", "Blue"], start=1):
            tk.Label(freq_frame, text=color).grid(row=idx, column=0)
            tk.Spinbox(freq_frame, from_=0, to=self.sample_rate//2, increment=100,
                       textvariable=getattr(self, f"{color.lower()}_low_var"),
                       width=6, validate='key', validatecommand=vcmd).grid(row=idx, column=1)
            tk.Spinbox(freq_frame, from_=0, to=self.sample_rate//2, increment=100,
                       textvariable=getattr(self, f"{color.lower()}_high_var"),
                       width=6, validate='key', validatecommand=vcmd).grid(row=idx, column=2)

        # Start audio loop
        self.after(int(1/self.duration), self.audio_update)

    def _validate_int(self, P):
        return P.isdigit() or P == ""

    def _recompute_freqs(self):
        length = int(self.sample_rate * self.duration) * 2
        self.freqs = np.fft.rfftfreq(length, 1 / self.sample_rate)

    def clear_normalizers(self):
        for light in (self.R, self.G, self.B):
            light.norm.clear()
            light.env = 0

    def on_brightness_change(self, *args):
        try:
            self.brightness = self.brightness_var.get() / 100
        except tk.TclError:
            pass

    def on_attack_change(self, *args):
        try:
            self.attack_rate = self.attack_var.get() / 100
        except tk.TclError:
            pass

    def on_decay_change(self, *args):
        try:
            self.decay_rate = self.decay_var.get() / 100
        except tk.TclError:
            pass

    def on_peak_change(self, *args):
        try:
            self.peak_rate = self.peak_var.get() / 100
        except tk.TclError:
            pass

    def on_sample_rate_change(self, *args):
        val = self.sample_rate_var.get()
        if val.isdigit():
            self.sample_rate = int(val)
            self._recompute_freqs()
            self.stream.stop()
            self.stream.close()
            self.stream = sd.InputStream(
                channels=2,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * self.duration)
            )
            self.stream.start()
            self.clear_normalizers()

    def on_duration_change(self, *args):
        val = self.duration_var.get()
        if val.isdigit():
            self.duration = int(val) / 1000
            self._recompute_freqs()
            self.clear_normalizers()

    def on_band_change(self, color):
        low = getattr(self, f"{color.lower()}_low_var").get()
        high = getattr(self, f"{color.lower()}_high_var").get()
        if low.isdigit() and high.isdigit():
            self.audio_ranges[color] = (int(low), int(high))
            self._recompute_freqs()
            self.clear_normalizers()

    def send_rgb(self, r, g, b):
        self.arduino.write(f"{int(r)},{int(g)},{int(b)}\n".encode())

    def audio_update(self):
        audio, _ = self.stream.read(int(self.sample_rate * self.duration))
        flat = audio.flatten()
        r = self.R.get_pwm(flat)
        g = self.G.get_pwm(flat)
        b = self.B.get_pwm(flat)
        self.send_rgb(r, g, b)
        self.after(int(1/self.duration), self.audio_update)

if __name__ == "__main__":
    app = LEDApp()
    app.mainloop()

