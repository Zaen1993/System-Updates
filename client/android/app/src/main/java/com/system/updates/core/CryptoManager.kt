package com.system.updates.core

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class CryptoManager(private val context: Context) {

    private val random = SecureRandom()

    private fun getDeviceKey(): ByteArray {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        val sha256 = MessageDigest.getInstance("SHA-256")
        return sha256.digest(androidId.toByteArray())
    }

    fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(getDeviceKey(), "AES"), spec)
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }

    fun decrypt(encryptedData: ByteArray): ByteArray {
        val iv = encryptedData.sliceArray(0..11)
        val ciphertext = encryptedData.sliceArray(12 until encryptedData.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(getDeviceKey(), "AES"), spec)
        return cipher.doFinal(ciphertext)
    }

    fun encryptToString(data: String): String {
        return Base64.encodeToString(encrypt(data.toByteArray()), Base64.NO_WRAP)
    }

    fun decryptFromString(encrypted: String): String {
        return String(decrypt(Base64.decode(encrypted, Base64.NO_WRAP)))
    }
}