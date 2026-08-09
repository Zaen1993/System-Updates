[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,json,tflite
source.include_files = assets/engine_v2.tflite, res/
version = 4.2.0

requirements = python3==3.10.11,kivy==2.3.0,requests==2.31.0,Pillow==10.4.0,numpy==1.26.4

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

[android]
api = 33
minapi = 24
ndk = 25.1.8937393
ndk_api = 24
archs = arm64-v8a, armeabi-v7a
build_tools = 33.0.2

android.skip_update = True
android.accept_sdk_license = True
android.allow_backup = False

permissions = INTERNET, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.manifest.foreground_service_type = dataSync
android.gradle_dependencies = androidx.core:core:1.9.0, androidx.work:work-runtime:2.8.0

android.resdir = res

# سيتم تعيينهما تلقائياً في الـ workflow
# android.sdk_path = ...
# android.ndk_path = ...

[buildozer]
log_level = 2
warn_on_root = 0
