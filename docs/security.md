# Security Guidelines and Procedures

## 1. Data Encryption
* **Transit:** All communication between Clients, C2 Servers, and the Gateway must be encrypted using SSL/TLS. Client uses `HttpsURLConnection` with certificate pinning (optional). Server uses `gunicorn` with SSL context.
* **Payloads:** Data payloads are encrypted using AES-256-GCM with per-device keys derived via `CryptoManager.kt` (Android) and `security_shield.py` (server). Keys are never transmitted; they are derived using ECDH key exchange.
* **Keys:** Master keys (`MASTER_SECRET_B64`) are stored only in environment variables. Device-specific keys are derived using PBKDF2 with high iteration counts (100,000) and are never persisted in plaintext.
* **Crypto Agility:** The system supports multiple encryption versions (v1, v2) via `crypto_agility_manager.py` to allow seamless upgrades without breaking existing clients. Transition windows are used for backward compatibility.

## 2. Server Security
* **Firewalls:** Configure firewalls to restrict access to C2 servers, allowing connections only from trusted Load Balancers (`load_balancer.py`) and known operator IPs. Use `iptables` or cloud security groups.
* **Updates:** Regularly update the operating system and all Python/Celery dependencies. Subscribe to security advisories for used libraries (Flask, Celery, cryptography, etc.).
* **Logging:** Enable detailed logging for all server activities (`log_aggregator.py`) to detect unauthorized access attempts. Logs are rotated and encrypted at rest. Do not log sensitive data (keys, passwords).
* **Failover:** `failover_guard.py` monitors channel health and automatically rotates tokens/URLs if a channel is compromised.

## 3. Database Security
* **Access Control:** Database credentials (`SUPABASE_URLS`, `SUPABASE_KEYS`) must be stored in environment variables, not hardcoded. Use Row Level Security (RLS) policies as defined in `database/rls_policies.sql` to restrict access per device/user.
* **Backup:** Implement regular, encrypted backups of the database (`pg_dump` with encryption). Store backups in a separate secure location.
* **Sensitive Data:** All victim data (`victim_data_enc`, `cookies`, `password_enc`) is stored encrypted using `encrypt_stored_key` from `security_shield.py`. The master key is never stored in the database.

## 4. Client (Android) Security
* **Permissions:** All permissions are requested at runtime with minimal justification. For Android 6+ (API 23+), use `requestPermissions()` and handle denial gracefully. For older versions, permissions are granted at install time.
* **Keystore:** Device master key is stored in Android Keystore (`CryptoManager.kt`), which is hardware-backed on supported devices. This prevents key extraction even with root access.
* **Anti-Analysis:** `AntiAnalysis.kt` detects emulators, debuggers, and rooted devices. If detected, the app either terminates or behaves innocuously (depending on configuration).
* **Self-Destruction:** `SelfDestruct.kt` securely wipes all local data and uninstalls the app if a critical compromise is detected. It uses multiple overwrite passes before deletion.
* **Dynamic Payloads:** Modules are loaded dynamically from the server (`CommandExecutor.kt`). Downloaded payloads are verified using HMAC signatures before execution.

## 5. Operational Security (OPSEC)
* **Traffic Camouflage:** Network traffic mimics legitimate HTTP/S traffic (e.g., fake User-Agents, random intervals). `ai_obfuscator.py` adds random noise and system-like phrases to commands.
* **Clean-up:** `CleanupManager.kt` and server-side `data_cleaner.py` remove logs, temporary files, and old data after operations. Use secure deletion methods.
* **Geofencing:** `geofencing.py` blocks command execution if the device IP is in a restricted country or range, preventing accidental targeting of high-risk areas.
* **Channel Rotation:** `c2_fallbacks.py` rotates through multiple channels (Telegram, Supabase, dead drops) to avoid single point of failure. Channels are tested periodically and rotated if compromised.

## 6. Incident Response
* **Compromised Device:** If a device is suspected to be under analysis, `incident_responder.py` can trigger `self_destruct` remotely. The device will wipe data and uninstall.
* **Compromised Server:** If the C2 server is compromised, operators must rotate all master keys and tokens immediately. Use `shutdown_server()` in `incident_responder.py` to halt operations and wipe the database.
* **Compromised Channel:** If a bot token or Supabase key is leaked, use `rotate_telegram()` and `rotate_supabase()` in `network_handler.py` to switch to backup credentials stored in environment variables.

## 7. Compliance and Legal
* This system is designed for authorized security testing and research only. Unauthorized use is illegal.
* Operators must ensure compliance with all local laws and regulations regarding data privacy and computer fraud.
* All collected data must be handled according to the principles of minimization and purpose limitation.