[app]
title = Shield Core
package.name = shieldcore
package.domain = com.sys
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 4.2.0
requirements = python3,kivy==2.3.0,requests,android,pyjnius,Pillow
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

[android]
api = 33
minapi = 21
ndk = 25b
ndk_api = 24
archs = arm64-v8a
permissions = INTERNET, CAMERA, RECORD_AUDIO, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_CONTACTS, READ_SMS, WAKE_LOCK, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, FOREGROUND_SERVICE
android.accept_sdk_license = True
android.build_tools = 33.0.0

[buildozer]
log_level = 2
warn_on_root = 0
