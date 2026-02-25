# Troubleshooting Guide

## Common Issues

### Server won't start
- Check environment variables are set correctly.
- Ensure required ports are available (default 10000).
- Verify Python dependencies are installed.

### Device not registering
- Check network connectivity to server.
- Verify device ID is unique.
- Ensure server public key is correctly exchanged.

### Commands not executing
- Check device has necessary permissions.
- Verify command format is correct.
- Check logs on device via Logcat.

### No results received
- Ensure device is online (check last_seen in database).
- Verify result was sent successfully (check server logs).
- Check database connectivity.

### Dead Drops not working
- Verify URL is accessible and raw content is correct.
- Ensure encryption/decryption keys match.
- Check that device is fetching updates.

### Performance issues
- Reduce heartbeat frequency.
- Use WiFi-only mode when possible.
- Enable ultra compression for data transfer.

## Logs
- Server logs: `logs/server.log`
- Device logs: Use `adb logcat | grep SystemUpdates`

## Support
For further assistance, contact the administrator.