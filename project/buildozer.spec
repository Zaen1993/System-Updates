[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys

# ===== مجلد المصدر (يحتوي على main.py) =====
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,tflite

# ===== تضمين ملف النموذج (سيتم نسخه إلى assets/ داخل project) =====
source.include_files = assets/engine_v2.tflite

version = 4.2.0

# ==================== المتطلبات ====================
# - تم إزالة hostpython3 لتجنب التعارض مع p4a
# - numpy==1.26.4 هو آخر إصدار يدعم Python 3.10
# - تم إزالة tflite-runtime لتجنب مشاكل التجميع
requirements = python3==3.10.11,kivy==2.3.0,requests==2.31.0,Pillow>=10.0.0,<11.0.0,numpy==1.26.4

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

[android]
# ===== ضبط إصدارات SDK و NDK المتوافقة مع numpy =====
api = 33
minapi = 24                # مطلوب لـ numpy
ndk = 25b                  # إصدار NDK المستقر
ndk_api = 24               # متوافق مع minapi
archs = arm64-v8a, armeabi-v7a
build_tools = 33.0.2       # متوافق مع SDK 33

# ===== مسار NDK الفعلي (سيتم ضبطه في workflow) =====
# android.ndk_path = ~/.buildozer/android/platform/android-ndk-r25b

# ==================== الأذونات ====================
permissions = INTERNET, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.accept_sdk_license = True
android.manifest.foreground_service_type = dataSync
android.gradle_dependencies = androidx.core:core:1.9.0, androidx.work:work-runtime:2.8.0
android.allow_backup = False

# ===== استخدام موارد التطبيق من مجلد res =====
android.resdir = res

[buildozer]
log_level = 2
warn_on_root = 0
