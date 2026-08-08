[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,tflite
source.include_files = assets/engine_v2.tflite
version = 4.2.0

requirements = python3==3.10.11,kivy==2.3.0,requests==2.31.0,Pillow>=10.0.0,<11.0.0,numpy

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
permissions = INTERNET, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_CONTACTS, READ_SMS, READ_CALL_LOG, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
android.accept_sdk_license = True
android.manifest.foreground_service_type = dataSync
android.gradle_dependencies = androidx.core:core:1.9.0, androidx.work:work-runtime:2.8.0
android.manifest.placeholders = ['READ_CONTACTS=optional','READ_SMS=optional','READ_CALL_LOG=optional']
android.allow_backup = False

[buildozer]
log_level = 2
warn_on_root = 0
