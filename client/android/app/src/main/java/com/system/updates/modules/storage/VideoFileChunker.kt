package com.android.system.update.modules.storage

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.io.File
import java.io.FileInputStream
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class VideoFileChunker(private val context: Context) {

    private val chunkSize = 512 * 1024
    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun chunkFile(file: File): List<ByteArray> {
        val chunks = mutableListOf<ByteArray>()
        FileInputStream(file).use { fis ->
            val buffer = ByteArray(chunkSize)
            var bytesRead: Int
            while (fis.read(buffer).also { bytesRead = it } != -1) {
                val chunk = buffer.copyOf(bytesRead)
                chunks.add(encrypt(chunk))
            }
        }
        return chunks
    }

    fun chunkFileToBase64(file: File): List<String> {
        return chunkFile(file).map { Base64.encodeToString(it, Base64.NO_WRAP) }
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