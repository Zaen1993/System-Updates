import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaFactory")

class MediaFactory:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._workers = []
        self._init_workers()

    def _init_workers(self):
        try:
            from . import face_processor
            self._workers.append(face_processor.FaceProcessor(self.config.get("face_model")))
        except ImportError as e:
            logger.debug(f"Face processor not available: {e}")

        try:
            from . import audio_synthesizer
            self._workers.append(audio_synthesizer.AudioSynthesizer(self.config.get("audio_model")))
        except ImportError as e:
            logger.debug(f"Audio synthesizer not available: {e}")

    def create_worker(self, worker_type: str, worker_name: str) -> Optional[Any]:
        logger.info(f"Creating worker of type: {worker_type} named: {worker_name}")
        worker = None
        if worker_type == "face":
            from . import face_processor
            worker = face_processor.FaceProcessor(self.config.get("face_model"))
        elif worker_type == "audio":
            from . import audio_synthesizer
            worker = audio_synthesizer.AudioSynthesizer(self.config.get("audio_model"))
        else:
            logger.error(f"Unknown worker type: {worker_type}")
            return None

        worker.name = worker_name
        self._workers.append(worker)
        return worker

    def get_active_workers(self) -> List[Any]:
        return self._workers

    def encrypt_config(self) -> str:
        serialized = json.dumps(self.config)
        encoded = base64.b64encode(serialized.encode()).decode()
        return encoded

    @classmethod
    def from_encrypted_config(cls, encrypted: str) -> "MediaFactory":
        decoded = base64.b64decode(encrypted).decode()
        config = json.loads(decoded)
        return cls(config)

if __name__ == "__main__":
    cfg = {
        "face_model": "models/face_v2.onnx",
        "audio_model": "models/audio_v1.pt"
    }
    factory = MediaFactory(cfg)
    worker = factory.create_worker("face", "worker_01")
    if worker:
        print(f"Worker created: {worker.name}")
    print(f"Active workers: {len(factory.get_active_workers())}")