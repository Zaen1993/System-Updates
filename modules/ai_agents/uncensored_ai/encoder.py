import logging
import numpy as np

logger = logging.getLogger(__name__)

class UltrasoundEncoder:
    def __init__(self, config=None):
        self.config = config or {}
        self.sample_rate = self.config.get("sample_rate", 44100)
        self.base_freq = self.config.get("base_freq", 19000)
        self.duration = self.config.get("duration", 0.1)
        self._validate_params()

    def _validate_params(self):
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.base_freq <= 0:
            raise ValueError("base_freq must be positive")
        if self.duration <= 0:
            raise ValueError("duration must be positive")

    def encode_data(self, data):
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            raise TypeError("data must be str or bytes")
        signal = self._modulate(data)
        return signal

    def _modulate(self, data_bytes):
        bits = ''.join(format(b, '08b') for b in data_bytes)
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration), endpoint=False)
        signal = np.array([], dtype=np.float32)
        for bit in bits:
            freq = self.base_freq if bit == '1' else self.base_freq // 2
            tone = 0.5 * np.sin(2 * np.pi * freq * t)
            signal = np.concatenate((signal, tone))
        return signal

if __name__ == "__main__":
    enc = UltrasoundEncoder()
    test = enc.encode_data("test")
    print(f"Encoded length: {len(test)}")