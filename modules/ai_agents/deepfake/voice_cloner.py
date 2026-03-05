import logging
from modules.ai_agents.deepfake import voice_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceCloner")

class VoiceCloner:
    def __init__(self, model_path):
        logger.info("Initializing voice cloning model...")
        self.model = voice_model.load_model(model_path)

    def generate(self, reference_audio, text, output_path):
        try:
            logger.info("Synthesizing voice clone...")
            self.model.synthesize(
                reference_audio=reference_audio,
                text=text,
                output_file=output_path
            )
            return True
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return False

if __name__ == "__main__":
    cloner = VoiceCloner("models/voice_model.pth")
    print("VoiceCloner ready.")