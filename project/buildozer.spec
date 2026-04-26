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

requirements = python3,kivy,requests,pillow,pyjnius,android

android.permissions = INTERNET, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, MANAGE_EXTERNAL_STORAGE, POST_NOTIFICATIONS

android.services = MyService:service.py
android.foreground = True
android.archs = arm64-v8a
android.release_minify = True
android.strip_libs = True
android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = "33.0.1"
android.uses_cleartext_traffic = True

fullscreen = 1
orientation = portrait
log_level = 2
warn_on_root = 0
