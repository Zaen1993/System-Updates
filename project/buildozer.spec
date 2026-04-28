[app]
title = Knox Attestation
package.name = knoxattestation
package.domain = com.samsung.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db
source.exclude_dirs = tests,__pycache__,docs,.github,.sys_runtime,g_tmp,ctmp,n_tmp,c_tmp,v_tmp,harvest
version = 2.5.1

requirements = python3,kivy,requests,urllib3,certifi,pillow,pyjnius,android,cryptography

icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, READ_CONTACTS, READ_SMS, SEND_SMS, MANAGE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO

android.api = 33
android.minapi = 24
android.accept_sdk_license = True
android.skip_update = True
android.auto_accept_sdk_license = True
android.archs = arm64-v8a

android.services = monitor:monitor.py
android.foreground = True
android.foreground_service_type = dataSync|camera|microphone
android.wakelock = True
android.uses_cleartext_traffic = True

orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

[buildozer]
log_level = 2
warn_on_root = 0
