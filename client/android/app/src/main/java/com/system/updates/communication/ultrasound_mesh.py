import json
import time
import hashlib
import base64
import threading
import queue
import logging
import random

try:
    import numpy as np
    import pyaudio
except ImportError:
    np = None
    pyaudio = None

logger = logging.getLogger(__name__)

class UltrasoundMesh:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.base_freq = self.config.get("base_freq", 19000)
        self.sample_rate = self.config.get("sample_rate", 44100)
        self.duration = self.config.get("duration", 0.1)
        self.hop_interval = self.config.get("hop_interval", 5)
        self.freq_range = self.config.get("freq_range", 2000)
        self.peers = {}
        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()
        self.running = False
        self.tx_thread = None
        self.rx_thread = None
        self.hop_thread = None
        self.pa = None
        self.stream_out = None
        self.stream_in = None
        self.secret = hashlib.sha256(str(time.time()).encode()).digest()
        self.current_freq = self.base_freq
        self._init_audio()

    def _init_audio(self):
        if not pyaudio:
            return
        try:
            self.pa = pyaudio.PyAudio()
            self.stream_out = self.pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=int(self.sample_rate * self.duration)
            )
            self.stream_in = self.pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=int(self.sample_rate * self.duration)
            )
        except Exception as e:
            logger.error(f"Audio init failed: {e}")

    def _generate_tone(self, freq, duration):
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * freq * t)
        return tone.astype(np.float32)

    def start(self):
        self.running = True
        self.tx_thread = threading.Thread(target=self._tx_loop, daemon=True)
        self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self.hop_thread = threading.Thread(target=self._hop_loop, daemon=True)
        self.tx_thread.start()
        self.rx_thread.start()
        self.hop_thread.start()
        logger.info("UltrasoundMesh started")

    def stop(self):
        self.running = False
        if self.stream_out:
            self.stream_out.stop_stream()
            self.stream_out.close()
        if self.stream_in:
            self.stream_in.stop_stream()
            self.stream_in.close()
        if self.pa:
            self.pa.terminate()
        logger.info("UltrasoundMesh stopped")

    def _hop_loop(self):
        while self.running:
            time.sleep(self.hop_interval)
            self.current_freq = self.base_freq + random.randint(-self.freq_range, self.freq_range)
            logger.debug(f"Hopped to {self.current_freq} Hz")

    def _tx_loop(self):
        while self.running:
            try:
                data = self.tx_queue.get(timeout=0.5)
                if data is None:
                    continue
                encrypted = self._encrypt(data)
                bits = ''.join(format(b, '08b') for b in encrypted)
                signal = np.array([], dtype=np.float32)
                t = np.linspace(0, self.duration, int(self.sample_rate * self.duration), endpoint=False)
                for bit in bits:
                    freq = self.current_freq if bit == '1' else self.current_freq // 2
                    tone = 0.5 * np.sin(2 * np.pi * freq * t)
                    signal = np.concatenate((signal, tone))
                if signal.size > 0:
                    self.stream_out.write(signal.tobytes())
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TX error: {e}")

    def _rx_loop(self):
        while self.running:
            try:
                chunk = self.stream_in.read(int(self.sample_rate * self.duration))
                data = np.frombuffer(chunk, dtype=np.float32)
                fft = np.fft.rfft(data)
                freqs = np.fft.rfftfreq(len(data), 1/self.sample_rate)
                mag = np.abs(fft)
                peak_idx = np.argmax(mag)
                detected = freqs[peak_idx]
                if abs(detected - self.current_freq) < 500:
                    self.rx_queue.put({"freq": detected, "time": time.time()})
            except Exception as e:
                logger.error(f"RX error: {e}")

    def _encrypt(self, data: bytes) -> bytes:
        key = self.secret
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

    def _decrypt(self, data: bytes) -> bytes:
        return self._encrypt(data)

    def send_data(self, device_id: str, data: bytes) -> bool:
        encrypted = self._encrypt(data)
        self.tx_queue.put(encrypted)
        return True

    def receive_data(self) -> list:
        msgs = []
        while not self.rx_queue.empty():
            msgs.append(self.rx_queue.get())
        return msgs

    def scan(self) -> list:
        devices = []
        for peer_id, info in self.peers.items():
            devices.append({"id": peer_id, "signal": info.get("signal", 0), "last_seen": info.get("last_seen")})
        return devices

    def get_signal_quality(self) -> int:
        return random.randint(50, 100)

    def status(self) -> dict:
        return {"running": self.running, "freq": self.current_freq, "peers": len(self.peers)}

    def register_peer(self, peer_id: str, info: dict):
        self.peers[peer_id] = info

    def process_task(self, task_type: str, data: any) -> dict:
        if task_type == "send":
            dev = data.get("device_id")
            payload = data.get("payload", "").encode()
            ok = self.send_data(dev, payload)
            return {"status": "ok" if ok else "fail"}
        elif task_type == "receive":
            return {"messages": self.receive_data()}
        elif task_type == "scan":
            return {"devices": self.scan()}
        return {"error": "Unknown task"}