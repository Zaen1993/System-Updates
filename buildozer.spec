[app]
title = Simple Service
package.name = simple_service
package.domain = com.test.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,xml
version = 1.0.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 33.0.0
android.archs = arm64-v8a
android.release_artifact = apk
android.accept_sdk_license = True
android.wakelock = False
android.num_cores = 1

[buildozer]
log_level = 2
warn_on_root = 1
