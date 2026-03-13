import logging
import secrets
import telebot
from supabase import create_client
from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not Config.TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")
bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)

try:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    logger.info("Supabase client created successfully")
except Exception as e:
    logger.error(f"Failed to create Supabase client: {e}")
    raise

@bot.message_handler(commands=['login'])
def login(message):
    args = message.text.split()
    if len(args) != 2 or args[1] != Config.MASTER_ENCRYPTION_KEY:
        bot.reply_to(message, "❌ Invalid Password.")
        return
    token = secrets.token_hex(16)
    try:
        supabase.table("sessions").upsert({
            "chat_id": message.chat.id,
            "session_token": token,
            "last_activity": "now()"
        }).execute()
        bot.reply_to(message, "✅ Authorized. Session Active.")
    except Exception as e:
        logger.error(f"Database error in login: {e}")
        bot.reply_to(message, "⚠️ Database error. Please try again later.")

@bot.message_handler(commands=['logout'])
def logout(message):
    try:
        supabase.table("sessions").delete().eq("chat_id", message.chat.id).execute()
        bot.reply_to(message, "🔒 Logged out successfully.")
    except Exception as e:
        logger.error(f"Error in logout: {e}")
        bot.reply_to(message, "⚠️ Error during logout.")

@bot.message_handler(func=lambda m: True)
def handle_commands(message):
    try:
        session_check = supabase.table("sessions").select("session_token").eq("chat_id", message.chat.id).execute()
        if not session_check.data:
            bot.reply_to(message, "⚠️ Login required: /login <password>")
            return
    except Exception as e:
        logger.error(f"Auth check failed: {e}")
        bot.reply_to(message, "⚠️ Authentication check failed.")
        return

    if message.text == "/clients":
        try:
            response = supabase.table("pos_clients").select("*").execute()
            if not response.data:
                bot.send_message(message.chat.id, "No devices found.")
                return
            msg_lines = ["📱 Active Devices:"]
            for device in response.data:
                serial = device.get("Client_serial", "Unknown")
                ip = device.get("Ip_address", "N/A")
                status = device.get("Operational_status", "offline")
                msg_lines.append(f"• SN: `{serial}` | IP: {ip} | Status: {status}")
            bot.send_message(message.chat.id, "\n".join(msg_lines), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error fetching devices: {e}")
            bot.send_message(message.chat.id, "⚠️ Failed to fetch devices.")
    else:
        bot.reply_to(message, "Unknown command. Use /login, /logout, or /clients.")

if __name__ == "__main__":
    logger.info("Bot started polling...")
    bot.infinity_polling()
