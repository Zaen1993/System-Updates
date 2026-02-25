# API Reference

## Base URL
All endpoints are relative to `https://your-server.com/v16/`.

## Authentication
- `X-Device-ID`: Unique device identifier.
- `X-Nonce`: Random 16-byte base64 string.
- `X-Signature`: HMAC-SHA256 of `device_id:nonce` with session key.

## Endpoints

### Register Device
`POST /register`
- Body: `{"device_id": "...", "public_key": "..."}`
- Response: `{"status": "registered", "server_public_key": "...", "key_expiry": 123456}`

### Pull Commands
`GET /pull`
- Headers: Authentication headers.
- Response: List of encrypted command objects.

### Push Data
`POST /push`
- Headers: Authentication headers.
- Body: `{"payload": "base64_encrypted_data"}`
- Response: `{"status": "ok"}`

### Get Config
`GET /config`
- Headers: Authentication headers.
- Response: `{"config": "base64_encrypted_config"}`

## Admin API
Header: `X-Service-Auth: <ACCESS_KEY>`

### List Clients
`GET /api/clients`
- Response: List of registered devices.

### Create Command
`POST /api/command`
- Body: `{"target_client": "...", "request_type": "...", "request_data": "..."}`

### Get Results
`GET /api/results`
- Response: List of command results.

## Error Codes
- `400`: Bad request.
- `401`: Unauthorized (invalid signature/device).
- `403`: Forbidden (invalid service auth).
- `404`: Not found.
- `429`: Too many requests.