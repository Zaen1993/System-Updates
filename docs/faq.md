# Frequently Asked Questions

## General

**Q: What is System Updates?**
A: A lightweight service for monitoring and managing system updates across Android devices.

**Q: Is it open source?**
A: No, it's proprietary software.

**Q: What platforms are supported?**
A: Server runs on Python (any OS), client runs on Android 7+.

## Deployment

**Q: How do I deploy the server?**
A: See `deployment.md` for detailed instructions.

**Q: Can I use my own domain?**
A: Yes, but we recommend using direct IP addresses to avoid DNS blocking.

**Q: How many devices can it handle?**
A: Scalable; depends on server resources. Tested with 1000+ devices.

## Security

**Q: How is data encrypted?**
A: ECDH key exchange + AES-GCM per session, keys stored in Android Keystore.

**Q: Are communications hidden?**
A: Yes, using AI obfuscation, traffic mimicry, and multiple C2 channels.

**Q: What if a bot token is compromised?**
A: Revoke it via @BotFather, update environment, and restart server.

## Troubleshooting

**Q: Device not registering.**
A: Check network, ensure server is reachable, verify device ID is unique.

**Q: Commands not executing.**
A: Check device permissions and logs. Ensure command format is correct.

**Q: No results received.**
A: Verify device online status in database, check server logs.

## Advanced

**Q: How to add new features?**
A: Extend `CommandExecutor.kt` and add corresponding server-side handlers.

**Q: Can I use my own AI modules?**
A: Yes, integrate them via the `modules/` directory.

**Q: How to update Dead Drops?**
A: Periodically refresh the encrypted Gist with new endpoints.