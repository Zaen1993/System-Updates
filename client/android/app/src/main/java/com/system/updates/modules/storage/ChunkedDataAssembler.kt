package com.android.system.update.modules.storage

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class ChunkedDataAssembler(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun assembleChunks(encryptedChunks: List<String>): ByteArray {
        val decryptedParts = mutableListOf<ByteArray>()
        for (chunk in encryptedChunks) {
            val data = Base64.decode(chunk, Base64.NO_WRAP)
            decryptedParts.add(decrypt(data))
        }
        val totalSize = decryptedParts.sumOf { it.size }
        val result = ByteArray(totalSize)
        var pos = 0
        for (part in decryptedParts) {
            System.arraycopy(part, 0, result, pos, part.size)
            pos += part.size
        }
        return result
    }

    fun assembleChunksToString(encryptedChunks: List<String>): String {
        val data = assembleChunks(encryptedChunks)
        return String(data)
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