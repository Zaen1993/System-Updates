# ==================== main_bot.py ====================
import telebot
import logging
import os
from multiprocessing import Process, Manager
from supabase import create_client, Client
from bot_commands_menu import setup_bot_menu

# Read tokens from environment (TELEGRAM_TOKEN_1 to TELEGRAM_TOKEN_10)
TELEGRAM_TOKENS = []
for i in range(1, 11):
    token = os.environ.get(f"TELEGRAM_TOKEN_{i}")
    if token:
        TELEGRAM_TOKENS.append(token.strip())

ACCESS_PASSWORD = os.environ.get("MASTER_PASSWORD", "Zaen123@123@")
SUPABASE_URL = os.environ.get("SUPABASE_URL_1")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY_1")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not TELEGRAM_TOKENS or not SUPABASE_URL:
    logger.error("Missing environment variables")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_bot(token, shared_auth_list):
    try:
        bot = telebot.TeleBot(token)
        logger.info(f"Starting bot with token: {token[:10]}...")

        @bot.message_handler(commands=['login'])
        def login(message):
            parts = message.text.split()
            if len(parts) == 2 and parts[1] == ACCESS_PASSWORD:
                if message.from_user.id not in shared_auth_list:
                    shared_auth_list.append(message.from_user.id)
                bot.reply_to(message, "✅ Authenticated. Use /menu.")
            else:
                bot.reply_to(message, "💀 Invalid password.")

        @bot.message_handler(commands=['block'])
        def block_admin(message):
            # Only allow if the requester is already admin
            if message.from_user.id not in shared_auth_list:
                return
            parts = message.text.split()
            if len(parts) != 3:
                bot.reply_to(message, "Usage: /block <target_user_id> <master_password>")
                return
            target_id, provided_pass = parts[1], parts[2]
            if provided_pass != ACCESS_PASSWORD:
                bot.reply_to(message, "❌ Incorrect master password.")
                return
            try:
                target_id = int(target_id)
                if target_id in shared_auth_list:
                    shared_auth_list.remove(target_id)
                    bot.reply_to(message, f"✅ User {target_id} has been removed from admins.")
                else:
                    bot.reply_to(message, "❌ User not found in admin list.")
            except ValueError:
                bot.reply_to(message, "❌ Invalid user ID.")

        @bot.message_handler(func=lambda message: True)
        def handle_all(message):
            if message.from_user.id not in shared_auth_list:
                return
            if message.text.startswith(('/menu', '/start')):
                setup_bot_menu(bot, message.from_user.id, supabase, auth_list=shared_auth_list)

        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Error in bot {token[:10]}: {e}")

if __name__ == "__main__":
    logger.info(f"Initializing {len(TELEGRAM_TOKENS)} bots...")
    # Reduce number of processes to 5 to save memory on Render free tier
    MAX_PROCESSES = min(5, len(TELEGRAM_TOKENS))
    with Manager() as manager:
        shared_auth_list = manager.list()
        processes = []
        for i in range(MAX_PROCESSES):
            p = Process(target=run_bot, args=(TELEGRAM_TOKENS[i], shared_auth_list))
            p.start()
            processes.append(p)
        for p in processes:
            p.join()
