# Frequently Asked Questions (FAQ)

## 1. General Questions

### Q: How can I add a new target device?
A: The target device needs to be compiled with the client-side code (`client/`) pointing to the Load Balancer IP address. Once installed, it will automatically check in.

### Q: What should I do if a target device status is "Offline"?
A: Ensure the device has an active internet connection. Check the C2 server logs for any incoming traffic from the device's IP.

### Q: How do I update the server configuration?
A: Modify the `.env` file and restart the server container.

## 2. Troubleshooting

### Q: I am getting "Connection Refused" errors on the dashboard.
A: This indicates that the Gateway Server (`/server/gateway/app.js`) is not running, or there is a firewall blocking port 3000.

### Q: Data from target devices is not showing up in the dashboard.
A: 1. Verify the `MASTER_SECRET_B64` in `crypto_utils.py` matches the one used by the client.  
   2. Check if the database (`c2_database`) is reachable and accepting connections.

### Q: The client app crashes on startup.
A: Check Android logcat for errors. Common causes: missing permissions, incompatible Android version (minSdk 21), or missing dependencies.

## 3. Security

### Q: Are the commands encrypted?
A: Yes, all commands and data payloads are encrypted using AES-GCM with per-device keys derived via PBKDF2.

### Q: What happens if a bot token is revoked?
A: The server will automatically rotate to the next available token. Update the `BOT_TOKENS` list in the environment.

## 4. Deployment

### Q: How do I deploy the server on Render?
A: Push the code to GitHub, connect your repository to Render, set the environment variables from `.env.example`, and deploy.

### Q: What databases are supported?
A: PostgreSQL is used for the main C2 data. SQLite is also supported for fallback.