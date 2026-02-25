#!/usr/bin/env python3
import numpy as np
import pyaudio
import time
import struct
import hashlib
import base64
from scipy import signal

class UltrasoundDecoder:
    def __init__(self, freq=19000, sample_rate=44100, duration=0.1, threshold=0.1):
        self.freq = freq
        self.sample_rate = sample_rate
        self.duration = duration
        self.threshold = threshold
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, input=True, frames_per_buffer=int(sample_rate * duration))

    def detect_freq(self, chunk):
        fft = np.fft.rfft(chunk)
        freqs = np.fft.rfftfreq(len(chunk), 1/self.sample_rate)
        mag = np.abs(fft)
        peak_idx = np.argmax(mag)
        return freqs[peak_idx]

    def decode(self, num_bits=8):
        bits = ""
        for _ in range(num_bits):
            chunk = self.stream.read(int(self.sample_rate * self.duration))
            data = np.frombuffer(chunk, dtype=np.float32)
            detected = self.detect_freq(data)
            if abs(detected - self.freq) < 1000:
                bits += "1"
            else:
                bits += "0"
        return bits

    def demodulate(self, bits):
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) == 8:
                chars.append(chr(int(byte, 2)))
        return ''.join(chars)

    def listen(self, length=64):
        bits = self.decode(length * 8)
        return self.demodulate(bits)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

if __name__ == "__main__":
    dec = UltrasoundDecoder()
    print("listening...")
    msg = dec.listen(8)
    print("received:", msg)
    dec.close()