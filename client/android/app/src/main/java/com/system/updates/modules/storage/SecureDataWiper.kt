package com.android.system.update.modules.storage

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.io.File
import java.io.RandomAccessFile
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SecureDataWiper(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun wipeFile(file: File): Boolean {
        return try {
            if (file.exists()) {
                val length = file.length()
                val buffer = ByteArray(4096)
                RandomAccessFile(file, "rws").use { raf ->
                    var pos: Long = 0
                    while (pos < length) {
                        random.nextBytes(buffer)
                        raf.write(buffer)
                        pos += buffer.size.toLong()
                    }
                }
                file.delete()
            } else false
        } catch (e: Exception) {
            false
        }
    }

    fun wipeAndReport(file: File): String {
        val success = wipeFile(file)
        val report = if (success) "wipe_success|${file.absolutePath}" else "wipe_fail|${file.absolutePath}"
        return encrypt(report)
    }

    private fun encrypt(data: String): String {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data.toByteArray())
        val combined = iv + encrypted
        return Base64.encodeToString(combined, Base64.NO_WRAP)
    }
}