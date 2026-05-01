[app]

# ====== هوية التطبيق ======
title = Ultra Secure Core
package.name = com.ultra.secure.v6
package.domain = ultra.secure
version = 5.2.0

# ====== المصادر ======
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*
source.exclude_dirs = tests, __pycache__, docs, .github, .sys_runtime

# ====== المكتبات (تم تغيير cryptography إلى إصدار لا يحتاج Rust) ======
requirements = python3, kivy==2.3.0, requests, urllib3, certifi, pillow, pyjnius, android, cryptography==3.4.8, pyzipper, numpy==1.26.4, tflite-runtime==2.14.0

# ====== أيقونة ======
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ====== صلاحيات Android (سطر واحد) ======
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CAMERA,RECORD_AUDIO,WAKE_LOCK,FOREGROUND_SERVICE,POST_NOTIFICATIONS,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,MANAGE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,READ_CONTACTS,READ_SMS,READ_CALL_LOG,FOREGROUND_SERVICE_DATA_SYNC,FOREGROUND_SERVICE_CAMERA,FOREGROUND_SERVICE_MICROPHONE

# ====== إعدادات SDK/NDK (بدون مسارات ثابتة) ======
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.build_tools_ver = 34.0.0
android.accept_sdk_license = True

# ====== المعمارية ======
android.archs = arm64-v8a

# ====== إعدادات الشبكة ======
android.allow_backup = False
android.request_legacy_external_storage = True
android.uses_cleartext_traffic = True

# ====== خدمات الخلفية ======
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True

# ====== واجهة ======
orientation = portrait
fullscreen = 1

# ====== البناء ======
log_level = 2
warn_on_root = 0

# ====== ميتا ======
android.meta_data = android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=1

# ====== تحسين ======
android.no_byte_compile_python = False
android.optimize_python = True

[buildozer]
log_level = 2
warn_on_root = 1
