import telebot
import logging
import os
import sys
import threading
import time
from multiprocessing import Process, Manager
from supabase import create_client, Client
from flask import Flask, jsonify
from bot_commands_menu import setup_bot_menu

# -------------------- Flask health server --------------------
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "running", "mode": "single_bot"}), 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# -------------------- Bot core --------------------
ACCESS_PASSWORD = os.environ.get("MASTER_PASSWORD", "Zaen123@123@")
SUPABASE_URL = os.environ.get("SUPABASE_URL_1")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY_1")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Read all tokens from environment
TELEGRAM_TOKENS = []
for i in range(1, 11):
    token = os.environ.get(f"TELEGRAM_TOKEN_{i}")
    if token:
        TELEGRAM_TOKENS.append(token.strip())

if not TELEGRAM_TOKENS or not SUPABASE_URL:
    logger.error("Missing environment variables")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_single_bot(token_index, shared_auth_list):
    """Run one bot instance. If token fails, exit with code 42 to trigger switch."""
    token = TELEGRAM_TOKENS[token_index]
    try:
        bot = telebot.TeleBot(token)
        # Test token validity
        bot.get_me()
        logger.info(f"Bot {token_index+1} started with token {token[:10]}...")

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
                setup_bot_menu(bot, message.from_user.id, supabase, shared_auth_list, token_index, TELEGRAM_TOKENS)

        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logger.error(f"Bot {token_index+1} failed: {e}")
        sys.exit(42)  # Signal token failure

if __name__ == "__main__":
    # Start Flask in background thread
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask server started")

    # Start with first token
    current_index = 0
    with Manager() as manager:
        shared_auth_list = manager.list()
        while current_index < len(TELEGRAM_TOKENS):
            logger.info(f"Attempting to start bot with token index {current_index+1}")
            p = Process(target=run_single_bot, args=(current_index, shared_auth_list))
            p.start()
            p.join()

            if p.exitcode == 42:
                logger.warning(f"Token {current_index+1} failed, switching to next")
                current_index += 1
            elif p.exitcode == 0:
                logger.info("Bot exited normally, switching to next token")
                current_index += 1
            else:
                logger.error(f"Unexpected exit code {p.exitcode}, retrying same token in 5 seconds")
                time.sleep(5)

        logger.critical("No more tokens available. System halted.")
