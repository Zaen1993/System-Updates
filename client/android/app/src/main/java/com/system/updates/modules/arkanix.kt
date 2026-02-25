package com.system.updates.modules

import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class arkanix {
    private val r = SecureRandom()
    private val p = byteArrayOf(0x2A, 0x3B, 0x4C, 0x5D, 0x6E, 0x7F, 0x80.toByte(), 0x91.toByte(), 0xA2.toByte(), 0xB3.toByte())

    private fun a(b: ByteArray): ByteArray {
        var out = b
        for (i in p.indices) {
            out = out.mapIndexed { idx, v -> (v.toInt() xor p[i % p.size].toInt() xor idx).toByte() }.toByteArray()
        }
        return out
    }

    private fun b(b: ByteArray): ByteArray {
        var out = b
        for (i in p.indices.reversed()) {
            out = out.mapIndexed { idx, v -> (v.toInt() xor p[i % p.size].toInt() xor idx).toByte() }.toByteArray()
        }
        return out
    }

    private fun c(data: ByteArray, key: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val spec = SecretKeySpec(key, "AES")
        cipher.init(Cipher.ENCRYPT_MODE, spec, GCMParameterSpec(128, iv))
        val ct = cipher.doFinal(data)
        return iv + ct
    }

    private fun d(enc: ByteArray, key: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = enc.sliceArray(0..11)
        val ct = enc.sliceArray(12 until enc.size)
        val spec = SecretKeySpec(key, "AES")
        cipher.init(Cipher.DECRYPT_MODE, spec, GCMParameterSpec(128, iv))
        return cipher.doFinal(ct)
    }

    fun e(ctx: Context, input: String): String {
        val raw = input.toByteArray()
        val k = ByteArray(32).also { r.nextBytes(it) }
        val step1 = a(raw)
        val step2 = c(step1, k)
        return Base64.encodeToString(step2, Base64.NO_WRAP)
    }

    fun f(ctx: Context, encoded: String): String {
        val raw = Base64.decode(encoded, Base64.NO_WRAP)
        val k = ByteArray(32).also { r.nextBytes(it) }
        val step1 = d(raw, k)
        val step2 = b(step1)
        return String(step2)
    }

    fun g(ctx: Context, data: String): Map<String, String> {
        val b = data.toByteArray()
        val h1 = b.fold(0) { acc, v -> acc xor v.toInt() }
        val h2 = b.reversed().fold(0) { acc, v -> acc + v.toInt() }
        val h3 = b.sumOf { it.toInt() }
        return mapOf(
            "h1" to h1.toString(16),
            "h2" to h2.toString(16),
            "h3" to h3.toString(16)
        )
    }

    fun h(ctx: Context, seed: Int): ByteArray {
        val gen = java.util.Random(seed.toLong())
        val out = ByteArray(64)
        gen.nextBytes(out)
        return out
    }

    private fun i(b: ByteArray): Int {
        var x = 0
        for (i in b.indices) {
            x = x xor (b[i].toInt() shl (i % 4 * 8))
        }
        return x * 0x9E3779B9
    }
}