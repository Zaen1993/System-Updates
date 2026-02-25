package com.system.updates.modules

import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class Force2FA {
    private val r = SecureRandom()
    private val k = byteArrayOf(0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0x6F, 0x70.toByte(), 0x81.toByte())

    private fun xor(b: ByteArray): ByteArray {
        return b.mapIndexed { i, v -> (v.toInt() xor k[i % k.size].toInt() xor i).toByte() }.toByteArray()
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

    fun trigger(ctx: Context, phoneNumber: String): String {
        val data = phoneNumber.toByteArray()
        val x = xor(data)
        val sessionKey = ByteArray(32).also { r.nextBytes(it) }
        val enc = aesEnc(x, sessionKey)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun verify(ctx: Context, code: String, token: String): Boolean {
        val enc = Base64.decode(token, Base64.NO_WRAP)
        val sessionKey = ByteArray(32).also { r.nextBytes(it) }
        val dec = aesDec(enc, sessionKey)
        val plain = xor(dec)
        val original = String(plain)
        return original.contains(code)
    }

    fun generateFakeSms(ctx: Context, target: String): String {
        val fake = "Your verification code is: ${r.nextInt(900000) + 100000}"
        val raw = fake.toByteArray()
        val x = xor(raw)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }
}