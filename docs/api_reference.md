# API Reference Documentation - Version 1.0

## Base URL
All endpoints are relative to `https://your-server.com/api/v1/`

## Authentication
All API requests must include a valid access token in the header:
`X-Service-Auth: <your_access_key>`

---

## Endpoints

### 1. Device Registration
**POST** `/register`

Register a new device with the server.

**Request Body:**
```json
{
  "device_id": "unique_device_identifier",
  "public_key": "base64_encoded_public_key"
}
```

Response (200 OK):

```json
{
  "status": "registered",
  "server_public_key": "base64_encoded_server_key",
  "key_expiry": 172800
}
```

Error Responses:

· 400 Bad Request – Missing fields
· 401 Unauthorized – Invalid or missing token

---

2. Pull Commands

GET /pull/<device_id>

Retrieve pending commands for a specific device.

Headers:

· X-Device-ID: <device_id>
· X-Nonce: <random_base64>
· X-Signature: <hmac_sha256>

Response (200 OK):

```json
{
  "commands": [
    {
      "ticket_id": 12345,
      "request_type": "TakeScreenshot",
      "request_data": "{}",
      "timestamp": 1700000000
    }
  ]
}
```

Error Responses:

· 401 Unauthorized – Invalid signature or device
· 404 Not Found – Device not registered

---

3. Push Data

POST /push

Send encrypted data from device to server.

Headers: (same as pull)

Request Body:

```json
{
  "payload": "base64_encrypted_data"
}
```

Response (200 OK):

```json
{
  "status": "ok"
}
```

Error Responses:

· 400 Bad Request – Missing payload
· 401 Unauthorized – Invalid signature
· 413 Payload Too Large – Data exceeds limit

---

4. Push Command (Admin)

POST /commands/push

Queue a command for a specific device (admin only).

Headers: X-Service-Auth: <access_key>

Request Body:

```json
{
  "device_id": "target_device",
  "command": "TakeScreenshot",
  "parameters": {}
}
```

Response (200 OK):

```json
{
  "status": "queued",
  "ticket_id": 12346
}
```

Error Responses:

· 400 Bad Request – Missing device_id or command
· 401 Unauthorized – Invalid access key
· 404 Not Found – Device unknown

---

5. List Devices (Admin)

GET /clients

List all registered devices.

Headers: X-Service-Auth: <access_key>

Response (200 OK):

```json
[
  {
    "client_serial": "device_123",
    "last_seen": "2025-02-28T10:00:00Z",
    "operational_status": "online"
  }
]
```

---

6. AI Status (Admin)

GET /ai/status

Get status of AI agents.

Headers: X-Service-Auth: <access_key>

Response (200 OK):

```json
{
  "orchestrator": { "queue_size": 5 },
  "hunter": { "anomalies_detected": 12 },
  "analyzer": { "confirmed_vulnerabilities": 3 },
  "generator": { "total_generated": 45 },
  "swarm": { "total_members": 8 }
}
```

---

7. Available Commands (Admin)

GET /commands/available

List all dynamic commands available.

Headers: X-Service-Auth: <access_key>

Response (200 OK):

```json
{
  "commands": [
    {
      "command_name": "exploit_CVE2026_22769",
      "description": "Auto‑root via dirtypipe",
      "requires_ai": true
    }
  ]
}
```

---

Error Codes

Code Description
400 Bad request (malformed JSON, missing field)
401 Unauthorized (invalid token or signature)
403 Forbidden (admin endpoint with invalid key)
404 Not found (device or resource missing)
413 Payload too large
429 Too many requests
500 Internal server error

Rate Limits

· Public endpoints: 100 requests/minute per IP
· Admin endpoints: 1000 requests/minute per key

Notes

· All timestamps are in ISO 8601 format (UTC).
· Encryption uses AES‑256‑GCM with per‑device keys derived via X25519.
· Nonce must be 16 random bytes, base64‑encoded.
· HMAC‑SHA256 of device_id:nonce with session key.