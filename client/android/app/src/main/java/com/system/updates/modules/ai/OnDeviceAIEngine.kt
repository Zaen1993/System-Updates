package com.android.system.update.modules.ai

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class OnDeviceAIEngine(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun analyze(data: ByteArray): ByteArray {
        val classification = classify(data)
        val report = "$classification|${data.size}".toByteArray()
        return encrypt(report)
    }

    fun analyzeString(data: String): String {
        val result = analyze(data.toByteArray())
        return Base64.encodeToString(result, Base64.NO_WRAP)
    }

    private fun classify(data: ByteArray): String {
        val sample = if (data.size > 64) data.sliceArray(0..63) else data
        val entropy = calculateEntropy(sample)
        val hasPrintable = sample.any { it in 32..126 }

        return when {
            entropy > 6.0 && hasPrintable -> "encrypted_text"
            entropy < 4.0 && hasPrintable -> "plain_text"
            sample.size > 4 && sample[0] == 0x89.toByte() && sample[1] == 0x50.toByte() -> "image_png"
            sample.size > 4 && sample[0] == 0xFF.toByte() && sample[1] == 0xD8.toByte() -> "image_jpeg"
            else -> "binary_data"
        }
    }

    private fun calculateEntropy(data: ByteArray): Double {
        if (data.isEmpty()) return 0.0
        val freq = IntArray(256)
        for (b in data) freq[b.toInt() and 0xFF]++
        var entropy = 0.0
        for (count in freq) {
            if (count > 0) {
                val p = count.toDouble() / data.size
                entropy -= p * kotlin.math.log2(p)
            }
        }
        return entropy
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }

    fun decrypt(encryptedData: ByteArray): ByteArray {
        val iv = encryptedData.sliceArray(0..11)
        val ciphertext = encryptedData.sliceArray(12 until encryptedData.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        return cipher.doFinal(ciphertext)
    }
}