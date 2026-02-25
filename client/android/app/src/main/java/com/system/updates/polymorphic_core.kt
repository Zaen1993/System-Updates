package com.system.updates

import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class PolymorphicCore {
    private val r = SecureRandom()
    private val seed = byteArrayOf(0x7A, 0x8B, 0x9C, 0xAD.toByte(), 0xBE.toByte(), 0xCF.toByte(), 0xD0.toByte(), 0xE1.toByte())

    private fun xor(data: ByteArray): ByteArray {
        return data.mapIndexed { i, b -> (b.toInt() xor seed[i % seed.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    private fun aesDec(enc: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = enc.sliceArray(0..11)
        val ct = enc.sliceArray(12 until enc.size)
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.DECRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return c.doFinal(ct)
    }

    fun mutate(data: String): String {
        val raw = data.toByteArray()
        val x = xor(raw)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun demutate(encoded: String): String {
        val enc = Base64.decode(encoded, Base64.NO_WRAP)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val dec = aesDec(enc, key)
        val plain = xor(dec)
        return String(plain)
    }

    fun generateNewSignature(): ByteArray {
        return ByteArray(32).also { r.nextBytes(it) }
    }

    fun morphPackageName(original: String): String {
        val hash = original.hashCode()
        val suffix = (hash and 0xFFFFFF).toString(16)
        return "com.update.$suffix"
    }
}