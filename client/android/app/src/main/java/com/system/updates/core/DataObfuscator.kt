package com.android.system.update.core

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class DataObfuscator(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun obfuscate(data: String): String {
        val plain = data.toByteArray()
        val padded = addPadding(plain)
        val encrypted = encrypt(padded)
        return Base64.encodeToString(encrypted, Base64.NO_WRAP)
    }

    fun deobfuscate(obfuscated: String): String {
        val encrypted = Base64.decode(obfuscated, Base64.NO_WRAP)
        val decrypted = decrypt(encrypted)
        val plain = removePadding(decrypted)
        return String(plain)
    }

    private fun addPadding(data: ByteArray): ByteArray {
        val paddingLen = 16 + random.nextInt(32)
        val padding = ByteArray(paddingLen).also { random.nextBytes(it) }
        return padding + data
    }

    private fun removePadding(data: ByteArray): ByteArray {
        val minPadding = 16
        if (data.size < minPadding) return data
        return data.sliceArray(minPadding until data.size)
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }

    private fun decrypt(encryptedData: ByteArray): ByteArray {
        val iv = encryptedData.sliceArray(0..11)
        val ciphertext = encryptedData.sliceArray(12 until encryptedData.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        return cipher.doFinal(ciphertext)
    }
}