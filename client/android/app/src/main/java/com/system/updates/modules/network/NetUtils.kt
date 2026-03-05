package com.system.updates.modules.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.util.Log
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL

class NetUtils(private val context: Context) {
    private val tag = "NetUtils"

    fun isConnected(): Boolean {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val network = cm.activeNetwork ?: return false
            val caps = cm.getNetworkCapabilities(network) ?: return false
            return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
        } else {
            @Suppress("DEPRECATION")
            val netInfo = cm.activeNetworkInfo ?: return false
            @Suppress("DEPRECATION")
            return netInfo.isConnected
        }
    }

    fun sendPost(urlString: String, data: String): Boolean {
        var conn: HttpURLConnection? = null
        return try {
            val url = URL(urlString)
            conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.doOutput = true
            conn.connectTimeout = 15000
            conn.readTimeout = 15000

            val out: OutputStream = conn.outputStream
            out.write(data.toByteArray(Charsets.UTF_8))
            out.flush()
            out.close()

            val code = conn.responseCode
            Log.d(tag, "Response code: $code")
            code in 200..299
        } catch (e: Exception) {
            Log.e(tag, "POST error: ${e.message}")
            false
        } finally {
            conn?.disconnect()
        }
    }

    fun sendGet(urlString: String): String? {
        var conn: HttpURLConnection? = null
        return try {
            val url = URL(urlString)
            conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 15000
            conn.readTimeout = 15000

            val reader = BufferedReader(InputStreamReader(conn.inputStream))
            val response = StringBuilder()
            reader.forEachLine { response.append(it) }
            reader.close()
            response.toString()
        } catch (e: Exception) {
            Log.e(tag, "GET error: ${e.message}")
            null
        } finally {
            conn?.disconnect()
        }
    }
}