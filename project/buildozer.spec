[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,json,tflite
source.include_files = assets/engine_v2.tflite, res/
version = 4.2.0

requirements = hostpython3==3.10,python3==3.10,kivy==2.3.0,Cython==0.29.33,requests==2.31.0,pillow,numpy

orientation = portrait
fullscreen = 0

[android]
api = $ANDROID_API
minapi = $ANDROID_MIN_API
ndk = 25b
ndk_api = $ANDROID_MIN_API
archs = arm64-v8a, armeabi-v7a
build_tools = 31.0.0

android.skip_update = True
android.accept_sdk_license = True
android.allow_backup = False

permissions = INTERNET, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE

android.manifest.foreground_service_type = dataSync
android.gradle_dependencies = androidx.core:core:1.9.0, androidx.work:work-runtime:2.8.0
android.resdir = res

# ============================================
# ✅ تم إضافة المسارات الصريحة لـ SDK و NDK
# ============================================
android.sdk_path = $ANDROID_HOME
android.ndk_path = $ANDROID_NDK_HOME

[buildozer]
log_level = 2
warn_on_root = 0
p4a.source_dir = /home/runner/work/System-Updates/System-Updates/project/.buildozer/android/platform/python-for-android
# السماح بتفاوت minsdk إذا لزم الأمر (احتياط)
p4a.extra_args = --allow-minsdk-ndkapi-mismatch
