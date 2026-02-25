package com.system.updates.modules

import android.content.Context
import android.net.wifi.WifiManager
import java.net.InetAddress

class NetworkScanner {
    fun scanLocalNetwork(): List<String> {
        val results = mutableListOf<String>()
        try {
            val wifiManager = Runtime.getRuntime().exec("ip route")
            val reader = wifiManager.inputStream.bufferedReader()
            val line = reader.readLine()
            reader.close()
            val parts = line.split(" ")
            val network = parts[0] ?: return results
            val prefix = network.substringBeforeLast(".")
            for (i in 1..254) {
                val host = "$prefix.$i"
                if (isReachable(host, 200)) {
                    results.add(host)
                }
            }
        } catch (e: Exception) {
            results.add("Scan error: ${e.message}")
        }
        return results
    }

    private fun isReachable(host: String, timeout: Int): Boolean {
        return try {
            val addr = InetAddress.getByName(host)
            addr.isReachable(timeout)
        } catch (e: Exception) {
            false
        }
    }
}