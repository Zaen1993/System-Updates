[app]
title = System Update
package.name = systemupdate
package.domain = org.system.update
version = 2.0.0
version.release = 2.0.0
icon.filename = %(source.dir)s/icon.png
icon.adaptive_foreground.filename = %(source.dir)s/icon.png
android.adaptive_icon_background = #FFFFFF

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db
source.exclude_dirs = tests, __pycache__, docs, examples, .github
source.exclude_patterns = *.pyc, *.pyo, *.pyd, *.so.debug, *.a, *.la

requirements = python3,kivy,requests,pillow,pyjnius,android,cryptography

android.permissions = INTERNET, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, MANAGE_EXTERNAL_STORAGE, POST_NOTIFICATIONS

android.accept_sdk_license = True
android.skip_update = True
android.ndk = 25b
android.api = 33
android.minapi = 21
android.build_tools_version = 33.0.1
android.archs = arm64-v8a

android.services = MyService:service.py
android.foreground = True
android.release_minify = True
android.strip_libs = True
android.uses_cleartext_traffic = True

fullscreen = 1
orientation = portrait
log_level = 2
warn_on_root = 0
