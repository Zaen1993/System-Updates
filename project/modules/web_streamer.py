import os
import base64
import requests
import time

def get_protected_token():
    secret = "S1BlMXM3WWZmWXdUVVI1ODpmV19rQ3lQV2dVQllhZmZWS3BYeFlKUmpjSnZDOTNC"[::-1]
    return base64.b64decode(secret).decode()

def setup_tunnel(port):
    try:
        bin_path = "./bin/ngrok"
        os.system(f"chmod +x {bin_path}")
        my_token = get_protected_token()
        os.system(f"{bin_path} config add-authtoken {my_token} > /dev/null 2>&1")
        os.system(f"{bin_path} http {port} --log=stdout > /dev/null 2>&1 &")
        time.sleep(10)
        try:
            r = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
            return r.json()['tunnels'][0]['public_url']
        except:
            return "⚠️ النفق يعمل ولكن لم يتم استلام الرابط بعد، جرب أمر الفحص مرة أخرى."
    except Exception as e:
        return f"❌ فشل أمني: {str(e)}"

def stop_tunnel():
    os.system("pkill ngrok")
    return "🛑 تم إغلاق النفق وتأمين الجهاز."
