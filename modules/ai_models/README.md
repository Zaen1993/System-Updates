# AI Models Directory

This directory contains pre-trained AI models used by various modules.

## Models

### Tiny CodeBERTa
- Location: `tiny_codeberta.pt`
- Size: ~15 MB
- Purpose: Code analysis and vulnerability detection
- Usage: Used by Shannon Lite module

### CodeBERTa-small
- Location: `codeberta-small.pt`
- Size: ~50 MB
- Purpose: Enhanced code analysis
- Usage: Fallback for Shannon Lite

### Voice Cloning Model
- Location: `voice_clone.pt`
- Size: ~100 MB
- Purpose: Voice synthesis for social engineering
- Usage: Used by VoiceCloner module

### Face Swapping Model
- Location: `face_swap.pt`
- Size: ~200 MB
- Purpose: Deepfake generation
- Usage: Used by FaceSwapper module

## Model Security

All model files are encrypted using AES-256 with a key derived from the master secret. They are decrypted only when loaded into memory.

## Adding New Models

1. Place the model file in this directory.
2. Update the corresponding module to load it.
3. Ensure encryption is applied.

## Notes

- Model files are not included in the repository due to size.
- They must be downloaded separately or generated via training scripts.