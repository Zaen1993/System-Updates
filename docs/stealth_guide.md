# Stealth and Anti-Detection Guide

## Overview
This document describes the stealth mechanisms integrated into the system to avoid detection by security software, analysis environments, and network monitoring.

## Core Principles
- **Polymorphism**: Code and signatures change periodically.
- **Mimicry**: Network traffic mimics legitimate applications.
- **Obfuscation**: Commands and data are hidden in plain sight.
- **Anti-Analysis**: Detection of emulators, debuggers, and security tools.

## Anti-Analysis Engine (`AntiAnalysis.kt`)
- Detects emulators (QEMU, Genymotion, Android emulator)
- Detects debuggers (JDWP, ptrace)
- Detects rooted devices (su binaries, test-keys)
- Detects security apps (Kaspersky, Avast, etc.)
- Self-destructs if analysis environment is confirmed

## Code Obfuscation (`ai_obfuscator.py`)
- Adds random noise and system-like phrases to commands
- Example: `"system: optimizing cache"` before actual command
- Commands are base64-encoded and rotated
- Mutation of patterns every 15 minutes

## Traffic Mimicry (`network_handler.py`)
- HTTP headers mimic Google Play Services, YouTube, or Gmail
- TLS fingerprints randomized
- Traffic timing randomized to avoid pattern detection
- Fallback to Tor or VPN in restricted regions

## Character Smuggling
- Zero-width characters (U+200B, U+200C, U+200D) hide data in plain text
- Commands embedded in comments, social media posts, or forum messages
- Decoder strips invisible characters and reconstructs command

## Icon Hiding
- App icon hidden from launcher after installation
- Optional: show fake system icon (gear, settings)
- Icon restored only if user manually opens app info

## Stealth Permissions
- Permissions requested at runtime with plausible excuses
- Example: "Camera permission needed for better video calls"
- No suspicious permissions requested at install time

## Self-Destruction
- If detected, app wipes all data and uninstalls itself
- Triggered after 60 days without server contact
- Can be remotely triggered via `/self_destruct` command

## Detection Evasion Techniques
- **Sandbox detection**: Check for common sandbox artifacts (files, processes)
- **Timing attacks**: Slow down execution in suspicious environments
- **Environment fingerprinting**: Compare hardware/software signatures

## Best Practices
- Always use encrypted channels (Telegram, Supabase, Dead Drops)
- Rotate C2 endpoints regularly
- Enable Tor bridges in censored regions
- Keep modules small and load dynamically

## Troubleshooting
- If app is detected, check `error_logs` for `ERR_ANTI_*` codes
- Verify that `AntiAnalysis.kt` is not triggering false positives
- Ensure obfuscation patterns are updated regularly