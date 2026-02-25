package com.system.updates.modules

import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.SecretKeySpec
import kotlin.math.*

class HybridObfuscator {
    private val rng = SecureRandom()
    private val p = arrayOf(
        "⚡","🔥","💧","🌍","🌙","☀️","⭐","❄️","🌈","⚡"
    )
    private val q = mapOf(
        "⚡" to 0x9E3779B9.toInt(),
        "🔥" to 0x85EBCA6B.toInt(),
        "💧" to 0xC2B2AE0D.toInt()
    )

    private fun l(t: ByteArray, k: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { rng.nextBytes(it) }
        val ks = SecretKeySpec(k, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, IvParameterSpec(iv))
        return iv + c.doFinal(t)
    }

    private fun i(b: ByteArray): String {
        val sb = StringBuilder()
        for (byte in b) {
            sb.append(p[byte.toInt().mod(p.size)])
        }
        return sb.toString()
    }

    private fun d(s: String): ByteArray {
        val b = ByteArray(s.length)
        for (i in s.indices) {
            val idx = p.indexOf(s[i].toString())
            b[i] = if (idx >= 0) idx.toByte() else 0
        }
        return b
    }

    fun y(ctx: Context, cmd: String): String {
        val x = cmd.toByteArray()
        val k = ByteArray(32).also { rng.nextBytes(it) }
        val e = l(x, k)
        val en = i(e)
        val dec = d(en)
        val n = kotlin.runCatching {
            Cipher.getInstance("AES/GCM/NoPadding").apply {
                init(Cipher.DECRYPT_MODE, SecretKeySpec(k, "AES"), IvParameterSpec(dec.sliceArray(0..11)))
            }.doFinal(dec.sliceArray(12 until dec.size))
        }.getOrNull() ?: return "ERR_DEC"
        val res = String(n)
        return if (res == cmd) "OK:${q.keys.random()}" else "ERR_MIS"
    }

    fun z(ctx: Context, data: ByteArray): ByteArray {
        val r1 = data.map { (it.toInt() xor 0xAA).toByte() }.toByteArray()
        val r2 = r1.reversedArray()
        val r3 = r2.mapIndexed { i, v -> (v.toInt() xor (i % 256)).toByte() }.toByteArray()
        val r4 = r3.copyOf()
        for (i in r4.indices step 2) {
            if (i + 1 < r4.size) {
                val t = r4[i]
                r4[i] = r4[i + 1]
                r4[i + 1] = t
            }
        }
        return r4
    }

    fun a(ctx: Context, input: String): Map<String, Any> {
        val b = input.toByteArray()
        val h1 = b.fold(0) { acc, v -> acc xor v.toInt() }
        val h2 = b.reversed().fold(0) { acc, v -> acc + v.toInt() }
        val h3 = sqrt(h2.toDouble()).toInt()
        val m = mutableMapOf<String, Any>()
        m["h1"] = h1
        m["h2"] = h2
        m["h3"] = h3
        m["⚡"] = q["⚡"] ?: 0
        m["🔥"] = q["🔥"] ?: 0
        return m
    }
}