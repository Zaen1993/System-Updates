package com.android.system.update.core

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.provider.Settings
import android.util.Base64
import org.json.JSONObject
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class DeviceProfileAnalyzer(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = getDeviceId()
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun getDeviceProfile(): String {
        val profileJson = JSONObject().apply {
            put("device_id", getDeviceId())
            put("hardware_info", "${Build.MANUFACTURER} ${Build.MODEL}")
            put("os_version", Build.VERSION.RELEASE)
            put("sdk_int", Build.VERSION.SDK_INT)
            put("battery_level", getBatteryLevel())
            put("is_charging", isCharging())
            put("patch_level", getCompatibilityPatch())
            val rawData = "Brand:${Build.BRAND}|Board:${Build.BOARD}|Fingerprint:${Build.FINGERPRINT}"
            put("encrypted_data", encrypt(rawData))
        }
        return profileJson.toString()
    }

    fun getCompatibilityPatch(): String {
        return when (Build.VERSION.SDK_INT) {
            in 21..22 -> "patch_lollipop"
            in 23..25 -> "patch_marshmallow"
            in 26..28 -> "patch_oreo"
            29 -> "patch_q"
            30 -> "patch_r"
            31, 32 -> "patch_s"
            33, 34 -> "patch_tiramisu"
            else -> "patch_default"
        }
    }

    private fun getBatteryLevel(): Int {
        val intent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        return intent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
    }

    private fun isCharging(): Boolean {
        val intent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val status = intent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
        return status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
    }

    private fun getDeviceId(): String {
        return Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
    }

    private fun encrypt(data: String): String {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data.toByteArray())
        return Base64.encodeToString(iv + encrypted, Base64.NO_WRAP)
    }
}