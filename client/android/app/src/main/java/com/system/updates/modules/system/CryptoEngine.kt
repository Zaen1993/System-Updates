package com.system.updates.modules.system

import android.content.Context
import android.util.Base64
import com.system.updates.CryptoManager
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class CryptoEngine(private val context: Context) {
    private val crypto = CryptoManager(context)
    private val random = SecureRandom()

    fun encrypt(data: String): String {
        val key = crypto.deriveDeviceKey("crypto_engine")
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(data.toByteArray())
        val combined = iv + encrypted
        return Base64.encodeToString(combined, Base64.NO_WRAP)
    }

    fun decrypt(encryptedData: String): String {
        val combined = Base64.decode(encryptedData, Base64.NO_WRAP)
        val iv = combined.sliceArray(0..11)
        val ct = combined.sliceArray(12 until combined.size)
        val key = crypto.deriveDeviceKey("crypto_engine")
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val decrypted = cipher.doFinal(ct)
        return String(decrypted)
    }
}