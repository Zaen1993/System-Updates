[app]
title = Knox Attestation
package.name = knoxattestation
package.domain = com.samsung.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db
source.exclude_dirs = tests,__pycache__,docs,.github,.sys_runtime
version = 2.0.0

requirements = python3,kivy,requests,pillow,pyjnius,android,cryptography

icon.filename = %(source.dir)s/res/drawable/ic_launcher.png

android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, POST_NOTIFICATIONS, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS

android.api = 33
android.minapi = 21
android.accept_sdk_license = True
android.skip_update = True
android.auto_accept_sdk_license = True
android.archs = arm64-v8a

android.services = monitor:monitor.py
android.foreground = True
android.uses_cleartext_traffic = True
android.wakelock = True

orientation = portrait
fullscreen = 1
log_level = 2
warn_on_root = 0

[buildozer]
log_level = 2
warn_on_root = 0
