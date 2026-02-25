# Security Guidelines

## Environment Variables

All secrets must be stored in environment variables, never in code. The following variables are required:

- `MASTER_SECRET_B64`: Base64-encoded 32-byte master secret.
- `SALT`: Random salt (minimum 16 bytes).
- `ADMIN_ID`: Telegram user ID of the administrator.
- `BOT_TOKENS`: Comma-separated Telegram bot tokens (10+ recommended).
- `SUPABASE_URLS`, `SUPABASE_KEYS`: Supabase project URLs and anon keys.
- `DEAD_DROP_URLS`: URLs of encrypted Dead Drops (GitHub Gists, Pastebin).
- `ACCESS_KEY`: Shared secret for API authentication.
- `USE_TOR`, `TOR_PROXY`: Optional Tor configuration.
- `USE_AI_C2`, `AI_C2_ENDPOINTS`: Optional AI-based C2 channels.
- `USE_BLOCKCHAIN`: Enable Blockchain C2 (requires web3 and a funded wallet).
- `USE_P2P`: Enable P2P network.
- `USE_MCP`: Enable MCP channel.

## Secure Communication

- All traffic between client and server is encrypted with AES‑GCM using per‑device keys derived via X25519.
- Each request includes an HMAC signature with a nonce to prevent replay attacks.
- Dead Drops are encrypted with the master key and stored on public platforms (GitHub Gists, Pastebin).

## Client Security

- The Android client stores its master key in the Android Keystore.
- Permissions are requested at runtime with plausible deniability messages.
- The app can self‑destruct if an analysis environment (emulator, debugger) is detected.
- Self‑healing mechanism can regenerate the app under a different name/icon after deletion.

## Blockchain C2 Security

- Blockchain transactions are public; commands must be encrypted.
- Use ephemeral wallets and avoid reusing addresses.
- For heartbeats, send minimal data (just a ping) to reduce cost and exposure.
- Consider mixing services (e.g., CoinJoin) if wallet tracking is a concern.

## P2P Network Security

- All P2P traffic is encrypted end‑to‑end.
- Use random intervals (beaconing) to avoid pattern detection.
- Devices should not trust all peers; implement a simple trust model or use a DHT.
- For local networks, keep traffic minimal and mimic normal protocols (e.g., WebRTC).

## Operational Security (OpSec)

- Rotate Telegram bots and Dead Drop URLs weekly.
- Use different IP addresses for the server (avoid DNS).
- Enable Tor or a VPN when operating in restricted regions.
- Never commit `.env` or any sensitive file to GitHub (`.gitignore` is provided).

## Incident Response

If a bot token is compromised:
1. Revoke the token via @BotFather.
2. Replace it in the environment variables and restart the server.
3. Update the Dead Drop with new tokens.

If the server IP is blocked:
1. Deploy a new instance on Render (or another cloud) with a different IP.
2. Update the Dead Drop with the new IP.
3. Clients will automatically fail over to the new address via Dead Drops.

If a blockchain wallet is compromised:
1. Move remaining funds to a new wallet.
2. Update the blockchain module with the new wallet address.
3. If using heartbeats, the wallet exposure is minimal.