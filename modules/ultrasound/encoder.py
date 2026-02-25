#!/usr/bin/env python3
import numpy as np
import pyaudio
import time
import struct
import hashlib
import base64

class UltrasoundEncoder:
    def __init__(self, freq=19000, sample_rate=44100, duration=0.1):
        self.freq = freq
        self.sample_rate = sample_rate
        self.duration = duration
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)

    def generate_tone(self, freq, duration):
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * freq * t)
        return tone.astype(np.float32)

    def modulate(self, data):
        bytes_data = data.encode() if isinstance(data, str) else data
        bits = ''.join(format(byte, '08b') for byte in bytes_data)
        signal = np.array([], dtype=np.float32)
        for bit in bits:
            if bit == '1':
                tone = self.generate_tone(self.freq, self.duration)
            else:
                tone = self.generate_tone(self.freq // 2, self.duration)
            signal = np.concatenate((signal, tone))
        return signal

    def encode(self, data):
        signal = self.modulate(data)
        self.stream.write(signal.tobytes())
        return len(signal)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

if __name__ == "__main__":
    enc = UltrasoundEncoder()
    enc.encode("test data")
    enc.close()