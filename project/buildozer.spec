[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,json,tflite
source.include_files = assets/engine_v2.tflite, res/
version = 4.2.0

# hostpython3 يُجبر على 3.10 لتطابق python3
requirements = hostpython3==3.10,python3==3.10,kivy==2.3.0,Cython==0.29.33,requests==2.31.0,pillow,numpy

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

[android]
api = 31
minapi = 24
ndk = 25b
ndk_api = 24
archs = arm64-v8a, armeabi-v7a
build_tools = 31.0.0

android.skip_update = True
android.accept_sdk_license = True
android.allow_backup = False

permissions = INTERNET, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.manifest.foreground_service_type = dataSync
android.gradle_dependencies = androidx.core:core:1.9.0, androidx.work:work-runtime:2.8.0

android.resdir = res

android.sdk_path = $ANDROID_HOME
android.ndk_path = $ANDROID_NDK_HOME

[buildozer]
log_level = 2
warn_on_root = 0
