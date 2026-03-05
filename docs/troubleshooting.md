# Troubleshooting Guide

## 1. Server Issues

### Server won't start
- Check environment variables in `.env` file
- Verify database connection string
- Check logs: `tail -f logs/server.log`
- Ensure ports are not in use: `netstat -tulpn | grep <port>`

### Database connection errors
- Verify PostgreSQL is running: `systemctl status postgresql`
- Check credentials in `.env`
- Test connection: `psql -h localhost -U <user> -d <dbname>`

### Celery workers not processing tasks
- Check Redis: `redis-cli ping`
- Restart workers: `celery -A tasks worker --loglevel=info`
- Check queue: `celery -A tasks inspect active`

## 2. Android Client Issues

### App crashes on startup
- Check AndroidManifest.xml permissions
- Verify minSdkVersion (21+)
- Check logcat: `adb logcat -s SystemUpdates`
- Test on different Android versions (8.0 to 14.0)

### Network connection failed
- Verify server URL in SharedPreferences
- Check internet permission
- Test with different network types (WiFi, mobile data)
- Ensure no firewall blocking

### Permissions not granted
- For Android 6.0+: request permissions at runtime
- For Android 10+: handle scoped storage correctly
- For Android 13+: new notification permission required
- Check permission handling in MainActivity

### Battery optimization blocking service
- Add to whitelist: `Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`
- Use foreground service with notification
- Test on Xiaomi, Huawei, Samsung (different manufacturers)

### Commands not executing
- Check command format in service_requests table
- Verify device has required permissions
- Check logs on device via Logcat
- Test with simple command first

## 3. Encryption Issues

### Data decryption fails on server
- Verify device ID matches
- Check key derivation algorithm (PBKDF2 with 100k iterations)
- Ensure AES-GCM tag is intact
- Test encryption/decryption locally first

### Android Keystore errors
- For Android 4.3-6.0: use different key algorithm
- For Android 7+: use Keystore properly
- Handle KeyPermanentlyInvalidatedException
- Fallback to software encryption if Keystore unavailable

## 4. Specific Manufacturer Issues

### Xiaomi/Redmi
- Auto-start permission required
- Add to protected apps list
- Show prompt to user: `Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)`
- Test with MIUI optimization off

### Huawei
- Protect app in battery settings
- Add to startup manager
- Handle EMUI specific intents
- Test without Google Play Services

### Samsung
- Disable auto-optimization for app
- Add to unmonitored apps list
- Test on One UI different versions
- Handle Knox container if present

## 5. Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| ERR_NETWORK | Network unreachable | Check internet, server URL |
| ERR_PERM | Permission denied | Request runtime permission |
| ERR_AUTH | Authentication failed | Verify device ID and signature |
| ERR_DECRYPT | Decryption failed | Check key derivation |
| ERR_DB | Database error | Verify connection |
| ERR_CMD | Command execution failed | Check command format |

## 6. Performance Issues

### High battery usage
- Reduce heartbeat frequency (30s → 60s)
- Use WorkManager instead of Service
- Batch data uploads
- Stop modules when not needed

### Memory leaks
- Check for unclosed cursors
- Release Camera/MediaRecorder properly
- Use WeakReference for callbacks
- Profile with Android Studio Memory Profiler

## 7. Debug Mode

Enable debug mode by setting `DEBUG_MODE=true` in `.env`

Then check:
- `logs/debug.log` for detailed logs
- `http://server:10000/debug` for status
- Device will send detailed reports to `/v16/debug`

## 8. Contact Support

If issues persist, contact administrator with:
- Device model and Android version
- Logs from `adb logcat -s SystemUpdates`
- Server logs from `/logs/server.log`
- Steps to reproduce