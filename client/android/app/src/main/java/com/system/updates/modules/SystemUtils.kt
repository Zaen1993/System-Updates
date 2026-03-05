package com.system.updates.modules.system

import android.content.Context
import android.os.Build
import android.provider.Settings
import android.util.Log
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader

class SystemUtils(private val context: Context) {
    private val tag = "SystemUtils"

    fun getDeviceId(): String {
        return Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
    }

    fun getSystemInfo(): Map<String, String> {
        val info = mutableMapOf<String, String>()
        info["model"] = Build.MODEL
        info["brand"] = Build.BRAND
        info["android_version"] = Build.VERSION.RELEASE
        info["sdk_version"] = Build.VERSION.SDK_INT.toString()
        info["manufacturer"] = Build.MANUFACTURER
        info["product"] = Build.PRODUCT
        info["hardware"] = Build.HARDWARE
        Log.i(tag, "System info collected")
        return info
    }

    fun hasRootAccess(): Boolean {
        val paths = arrayOf(
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su"
        )
        for (path in paths) {
            if (File(path).exists()) return true
        }
        val magisk = File("/sbin/.magisk")
        if (magisk.exists()) return true
        return false
    }

    fun executeShellCommand(command: String): String {
        return try {
            val process = Runtime.getRuntime().exec(command)
            val reader = BufferedReader(InputStreamReader(process.inputStream))
            val output = StringBuilder()
            reader.use { r ->
                r.forEachLine { line ->
                    output.append(line).append("\n")
                }
            }
            process.waitFor()
            output.toString()
        } catch (e: Exception) {
            Log.e(tag, "Shell exec error: ${e.message}")
            ""
        }
    }

    fun getScreenDimensions(): Pair<Int, Int> {
        val metrics = context.resources.displayMetrics
        return Pair(metrics.widthPixels, metrics.heightPixels)
    }

    fun getBatteryLevel(): Int {
        val batteryManager = context.getSystemService(Context.BATTERY_SERVICE) as android.os.BatteryManager
        return batteryManager.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }

    fun isEmulator(): Boolean {
        return (Build.BRAND.startsWith("generic") && Build.DEVICE.startsWith("generic")) ||
                Build.FINGERPRINT.startsWith("generic") ||
                Build.FINGERPRINT.startsWith("unknown") ||
                Build.MODEL.contains("google_sdk") ||
                Build.MODEL.contains("Emulator") ||
                Build.MODEL.contains("Android SDK built for x86") ||
                Build.MANUFACTURER.contains("Genymotion") ||
                Build.PRODUCT == "sdk" ||
                Build.PRODUCT == "google_sdk"
    }

    fun getStorageInfo(): Map<String, Long> {
        val info = mutableMapOf<String, Long>()
        val stats = android.os.StatFs(android.os.Environment.getDataDirectory().path)
        val blockSize = stats.blockSizeLong
        info["total"] = stats.blockCountLong * blockSize
        info["free"] = stats.availableBlocksLong * blockSize
        info["used"] = info["total"]!! - info["free"]!!
        return info
    }
}