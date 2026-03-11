# ==================== bot_handler.py ====================
import telebot
import secrets
from config import Config
from supabase import create_client

if not Config.BOT_TOKENS:
    raise ValueError("No bot tokens found in environment variables")
bot = telebot.TeleBot(Config.BOT_TOKENS[0])

sup_config = Config.SUPABASE[0]
if not sup_config["url"] or not sup_config["key"]:
    raise ValueError("Supabase credentials missing")
sb = create_client(sup_config["url"], sup_config["key"])

@bot.message_handler(commands=['login'])
def login(message):
    args = message.text.split()
    if len(args) != 2 or args[1] != Config.MASTER_PASS:
        bot.reply_to(message, "❌ Invalid Password.")
        return
    token = secrets.token_hex(16)
    try:
        sb.table("sessions").upsert({
            "chat_id": message.chat.id,
            "session_token": token
        }).execute()
        bot.reply_to(message, "✅ Authorized. Session Active.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Database error: {e}")

@bot.message_handler(commands=['logout'])
def logout(message):
    try:
        sb.table("sessions").delete().eq("chat_id", message.chat.id).execute()
        bot.reply_to(message, "🔒 Logged out successfully.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(func=lambda m: True)
def handle_commands(message):
    try:
        check = sb.table("sessions").select("session_token").eq("chat_id", message.chat.id).execute()
        if not check.data:
            bot.reply_to(message, "⚠️ Login required: /login <pass>")
            return
    except Exception as e:
        bot.reply_to(message, f"⚠️ Auth check failed: {e}")
        return

    if message.text == "/clients":
        try:
            res = sb.table("pos_clients").select("client_serial, ip_address, operational_status").execute()
            if not res.data:
                bot.send_message(message.chat.id, "No devices found.")
                return
            msg_lines = ["📱 Active Devices:"]
            for d in res.data:
                msg_lines.append(f"• SN: `{d['client_serial']}` | IP: {d['ip_address']} | Status: {d['operational_status']}")
            bot.send_message(message.chat.id, "\n".join(msg_lines), parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"⚠️ Error fetching devices: {e}")

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
