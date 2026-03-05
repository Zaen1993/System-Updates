package com.system.updates.modules.network

import android.content.Context
import android.os.Build
import android.provider.Settings
import android.util.Log
import java.io.File

class SandboxDetector(private val context: Context) {
    private val TAG = "SandboxDetector"
    private var isSandboxChecked = false
    private var cachedResult = false

    fun isSandboxDetected(): Boolean {
        if (isSandboxChecked) return cachedResult
        Log.d(TAG, "Checking for sandbox environment...")
        val result = checkBuildProps() || checkFileSystem() || checkEmulatorSettings() || checkHardware()
        isSandboxChecked = true
        cachedResult = result
        return result
    }

    private fun checkBuildProps(): Boolean {
        val fingerprint = Build.FINGERPRINT.lowercase()
        val model = Build.MODEL.lowercase()
        val manufacturer = Build.MANUFACTURER.lowercase()
        val board = Build.BOARD.lowercase()
        val device = Build.DEVICE.lowercase()
        val product = Build.PRODUCT.lowercase()
        val hardware = Build.HARDWARE.lowercase()
        val tags = Build.TAGS.lowercase()
        val type = Build.TYPE.lowercase()

        val markers = listOf("goldfish", "ranchu", "sdk", "vbox", "qemu", "androidvm", "generic")
        for (m in markers) {
            if (fingerprint.contains(m) || model.contains(m) || manufacturer.contains(m) ||
                board.contains(m) || device.contains(m) || product.contains(m) ||
                hardware.contains(m) || tags.contains(m) || type.contains(m)) {
                Log.w(TAG, "Sandbox detected via build prop: $m")
                return true
            }
        }
        return false
    }

    private fun checkFileSystem(): Boolean {
        val suspiciousFiles = listOf(
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su",
            "/sbin/.magisk",
            "/data/local/tmp/",
            "/system/etc/init.d/"
        )
        for (path in suspiciousFiles) {
            if (File(path).exists()) {
                Log.w(TAG, "Sandbox/root detected via file: $path")
                return true
            }
        }
        return false
    }

    private fun checkEmulatorSettings(): Boolean {
        val androidId = try {
            Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        } catch (e: Exception) {
            null
        }
        if (androidId.isNullOrEmpty()) return true

        val operatorName = Settings.Secure.getString(context.contentResolver, "operator_name")
        if (operatorName == "android") return true

        return false
    }

    private fun checkHardware(): Boolean {
        if (Build.HARDWARE.lowercase().contains("ranchu")) return true
        if (Build.PRODUCT.lowercase().contains("sdk")) return true
        if (Build.BOARD.lowercase().contains("sdk")) return true
        if (Build.FINGERPRINT.lowercase().contains("generic")) return true
        return false
    }
}