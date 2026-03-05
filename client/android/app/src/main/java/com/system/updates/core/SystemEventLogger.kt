package com.android.system.update.core

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.io.File
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SystemEventLogger(private val context: Context) {

    private val logFileName = "system_events.log"
    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun logEvent(event: String) {
        try {
            val encrypted = encrypt(event.toByteArray())
            val file = File(context.filesDir, logFileName)
            file.appendBytes(encrypted + "\n".toByteArray())
        } catch (e: Exception) {
        }
    }

    fun readEvents(): List<String> {
        val file = File(context.filesDir, logFileName)
        if (!file.exists()) return emptyList()
        return try {
            val lines = file.readLines()
            lines.mapNotNull { line ->
                try {
                    val decoded = Base64.decode(line, Base64.NO_WRAP)
                    String(decrypt(decoded))
                } catch (e: Exception) {
                    null
                }
            }
        } catch (e: Exception) {
            emptyList()
        }
    }

    fun clearLogs() {
        File(context.filesDir, logFileName).delete()
    }

    fun secureWipe() {
        val file = File(context.filesDir, logFileName)
        if (!file.exists()) return
        try {
            val length = file.length().toInt()
            val randomData = ByteArray(length).also { random.nextBytes(it) }
            file.writeBytes(randomData)
            file.delete()
        } catch (e: Exception) {
            file.delete()
        }
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data)
        val combined = iv + encrypted
        return Base64.encode(combined, Base64.NO_WRAP)
    }

    private fun decrypt(encryptedData: ByteArray): ByteArray {
        val raw = Base64.decode(encryptedData, Base64.NO_WRAP)
        val iv = raw.sliceArray(0..11)
        val ciphertext = raw.sliceArray(12 until raw.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        return cipher.doFinal(ciphertext)
    }
}