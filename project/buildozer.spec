[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,tflite
source.include_files = assets/engine_v2.tflite
version = 4.2.0

# تم إضافة tflite-runtime وتثبيته من PyPI مباشرة
requirements = python3==3.10.11,kivy==2.3.0,requests==2.31.0,Pillow>=10.0.0,<11.0.0,numpy,tflite-runtime==2.14.0

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

# تم حذف الصلاحيات غير الضرورية (READ_CONTACTS, READ_SMS, READ_CALL_LOG, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
permissions = INTERNET, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.accept_sdk_license = True
android.manifest.foreground_service_type = dataSync
android.gradle_dependencies = androidx.core:core:1.9.0, androidx.work:work-runtime:2.8.0
android.allow_backup = False

# إزالة android.manifest.placeholders لأنه لم يعد هناك صلاحيات اختيارية
# android.manifest.placeholders = []

[buildozer]
log_level = 2
warn_on_root = 0
