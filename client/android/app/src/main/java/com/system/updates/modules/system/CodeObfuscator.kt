package com.system.updates.modules.system

import android.util.Base64
import com.system.updates.CryptoManager
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class CodeObfuscator(private val crypto: CryptoManager) {
    private val random = SecureRandom()

    fun obfuscateString(plain: String): String {
        val key = crypto.deriveDeviceKey("obfuscate")
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val ct = cipher.doFinal(plain.toByteArray())
        val full = iv + ct
        return Base64.encodeToString(full, Base64.NO_WRAP)
    }

    fun deobfuscateString(obf: String): String {
        val key = crypto.deriveDeviceKey("obfuscate")
        val full = Base64.decode(obf, Base64.NO_WRAP)
        val iv = full.sliceArray(0..11)
        val ct = full.sliceArray(12 until full.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        return String(cipher.doFinal(ct))
    }

    fun insertJunkCode(): String {
        val junk = StringBuilder()
        for (i in 0..random.nextInt(5) + 3) {
            val a = random.nextInt()
            val b = random.nextInt()
            val c = a * b
            junk.append("junk_$i").append(c).append(";")
        }
        return junk.toString()
    }

    fun randomIdentifier(length: Int = 8): String {
        val chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return (1..length).map { chars[random.nextInt(chars.length)] }.joinToString("")
    }

    fun obfuscateNames(original: String): String {
        return original.replace(Regex("[a-zA-Z_][a-zA-Z0-9_]*")) {
            if (it.value.length > 2 && it.value[0].isLowerCase()) {
                randomIdentifier(it.value.length)
            } else it.value
        }
    }
}