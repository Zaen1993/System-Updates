"""
telegram/webhook.py
استقبال أوامر Telegram عبر Webhook (بديل Polling).
يتم تشغيل خادم HTTP صغير لاستقبال التحديثات من Telegram.
"""

import threading
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class WebhookHandler(BaseHTTPRequestHandler):
    """معالج طلبات HTTP الواردة من Telegram."""

    def do_POST(self):
        """معالجة طلب POST (الإرسال من Telegram)."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            update = json.loads(post_data.decode('utf-8'))
            # تمرير التحديث إلى معالج الأوامر (يتم تعيينه لاحقاً)
            if hasattr(self.server, 'command_handler'):
                self.server.command_handler.process_update(update)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        except Exception as e:
            print(f"Webhook error: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        """رد بسيط للتحقق من أن الخادم يعمل."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Webhook server is running.')

    def log_message(self, format, *args):
        # تعطيل تسجيل الطلبات في السجل
        pass

class WebhookServer:
    """
    خادم Webhook لتلقي الأوامر من Telegram.
    يتم تشغيله في خيط منفصل على منفذ محدد.
    """

    def __init__(self, command_handler, port=8443, host='0.0.0.0'):
        self.command_handler = command_handler
        self.port = port
        self.host = host
        self.server = None
        self.thread = None
        self.running = False

    def start(self):
        """بدء تشغيل الخادم في خيط منفصل."""
        if self.running:
            return
        self.server = HTTPServer((self.host, self.port), WebhookHandler)
        self.server.command_handler = self.command_handler
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        self.running = True
        print(f"Webhook server started on {self.host}:{self.port}")

    def _serve(self):
        """حلقة تشغيل الخادم."""
        try:
            self.server.serve_forever()
        except Exception as e:
            print(f"Webhook server error: {e}")

    def stop(self):
        """إيقاف الخادم."""
        if self.server and self.running:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            print("Webhook server stopped.")

    def set_webhook_url(self, bot_token, webhook_url):
        """إخبار Telegram بإرسال التحديثات إلى عنوان الـ Webhook."""
        import requests
        api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        try:
            response = requests.post(api_url, json={"url": webhook_url}, timeout=10)
            if response.status_code == 200:
                print("Webhook set successfully.")
                return True
            else:
                print(f"Failed to set webhook: {response.text}")
                return False
        except Exception as e:
            print(f"Error setting webhook: {e}")
            return False

    def delete_webhook(self, bot_token):
        """حذف الـ Webhook (العودة إلى Polling)."""
        import requests
        api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        try:
            requests.post(api_url, timeout=5)
            print("Webhook deleted.")
        except:
            pass

# دالة مساعدة لبدء Webhook بسهولة
def start_webhook(command_handler, bot_token, public_url, port=8443):
    """
    :param command_handler: كائن يحتوي على process_update(update)
    :param bot_token: توكن البوت
    :param public_url: الرابط العام للـ Webhook (مثل https://your-domain.com:8443)
    :param port: المنفذ المحلي (يجب أن يتطابق مع المنفذ في public_url)
    """
    server = WebhookServer(command_handler, port=port)
    server.start()
    server.set_webhook_url(bot_token, public_url)
    return server
