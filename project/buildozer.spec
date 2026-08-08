[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,tflite
source.include_files = assets/engine_v2.tflite
version = 4.2.0

# ==================== المتطلبات ====================
# تم حذف hostpython3 نهائياً كما هو مطلوب.
# تم تحديد python3 مع الإصدار المطلوب (إذا لم يقبله buildozer، يمكن حذف ==3.10.11 واكتفاء بـ python3)
# تم ترتيب المكتبات حسب الأهمية مع تحديد إصدارات مستقرة.
requirements = python3==3.10.11,kivy==2.3.0,requests==2.31.0,Pillow>=10.0.0,<11.0.0,numpy,tflite-runtime==2.14.0

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

[android]
api = 33
minapi = 21
ndk = 25.1.8937393
ndk_api = 24
archs = arm64-v8a, armeabi-v7a
build_tools = 33.0.0

# ==================== الأذونات ====================
# تم حذف الأذونات غير الضرورية المذكورة (READ_CONTACTS, READ_SMS, READ_CALL_LOG, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
# مع الاحتفاظ بالأذونات الأساسية للتطبيق.
permissions = INTERNET, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.accept_sdk_license = True
android.manifest.foreground_service_type = dataSync
android.gradle_dependencies = androidx.core:core:1.9.0, androidx.work:work-runtime:2.8.0
android.allow_backup = False

# ==================== ملاحظات إضافية ====================
# - تمت إزالة android.manifest.placeholders حيث لم تعد هناك أذونات اختيارية.
# - إذا واجهت مشكلة في تحديد إصدار python3، استخدم "python3" فقط.
# - يُنصح بإضافة متطلب "android" لبعض الميزات إذا لزم الأمر.

[buildozer]
log_level = 2
warn_on_root = 0
