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

class SecureStorageManager(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun saveEncryptedFile(fileName: String, data: ByteArray): Boolean {
        return try {
            val encrypted = encrypt(data)
            val file = File(context.filesDir, fileName)
            file.writeBytes(encrypted)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun readEncryptedFile(fileName: String): ByteArray? {
        return try {
            val file = File(context.filesDir, fileName)
            if (!file.exists()) return null
            val encrypted = file.readBytes()
            decrypt(encrypted)
        } catch (e: Exception) {
            null
        }
    }

    fun deleteFile(fileName: String): Boolean {
        return try {
            File(context.filesDir, fileName).delete()
        } catch (e: Exception) {
            false
        }
    }

    fun listFiles(): List<String> {
        return context.filesDir.listFiles()?.map { it.name } ?: emptyList()
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

    fun saveEncryptedString(fileName: String, data: String): Boolean {
        return saveEncryptedFile(fileName, data.toByteArray())
    }

    fun readEncryptedString(fileName: String): String? {
        return readEncryptedFile(fileName)?.let { String(it) }
    }
}