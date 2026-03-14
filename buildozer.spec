[app]
title = System Framework
package.name = system_update_service
package.domain = org.test.updates
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.1
requirements = python3,kivy==2.3.0,requests,python-dotenv
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.private_storage = True
android.entrypoint = main.py
android.foreground_service = True
android.archs = arm64-v8a
android.allow_backup = False
android.manifest.launch_mode = singleInstance
android.accept_sdk_license = True
android.wakelock = True

[buildozer]
log_level = 2
warn_on_root = 1
