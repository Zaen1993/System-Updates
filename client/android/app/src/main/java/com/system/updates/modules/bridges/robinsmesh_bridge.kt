package com.system.updates.modules.bridges

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import com.system.updates.core.CryptoManager
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class RobinsmeshBridge(private val context: Context) {

    private val TAG = "RobinsmeshBridge"
    private var cryptoManager: CryptoManager? = null
    private var nativeLoaded = false

    companion object {
        init {
            try {
                System.loadLibrary("robinsmesh_native")
                Log.d("RobinsmeshBridge", "Native library 'robinsmesh_native' loaded.")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("RobinsmeshBridge", "Failed to load native library: ${e.message}")
            }
        }
    }

    // Native functions
    private external fun startMeshNodeNative(nodeId: String): Boolean
    private external fun sendDataToPeerNative(peerId: String, data: ByteArray): Boolean
    private external fun receiveDataFromPeersNative(): ByteArray?
    private external fun stopMeshNodeNative(): Boolean

    init {
        nativeLoaded = try {
            startMeshNodeNative("test") // dummy call to check if native works
            true
        } catch (e: UnsatisfiedLinkError) {
            false
        }
        cryptoManager = CryptoManager(context)
        Log.d(TAG, "RobinsmeshBridge initialized. Native loaded: $nativeLoaded")
    }

    fun initialize(): Boolean {
        if (!checkPermissions()) {
            Log.e(TAG, "Missing required permissions")
            return false
        }
        return true
    }

    private fun checkPermissions(): Boolean {
        val permissions = mutableListOf<String>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions.add(Manifest.permission.BLUETOOTH_SCAN)
            permissions.add(Manifest.permission.BLUETOOTH_ADVERTISE)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
            permissions.add(Manifest.permission.NEARBY_WIFI_DEVICES)
        } else {
            permissions.add(Manifest.permission.BLUETOOTH)
            permissions.add(Manifest.permission.BLUETOOTH_ADMIN)
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
            permissions.add(Manifest.permission.ACCESS_COARSE_LOCATION)
        }
        permissions.add(Manifest.permission.ACCESS_NETWORK_STATE)
        permissions.add(Manifest.permission.CHANGE_WIFI_MULTICAST_STATE)
        permissions.add(Manifest.permission.CHANGE_WIFI_STATE)

        for (perm in permissions) {
            if (ContextCompat.checkSelfPermission(context, perm) != PackageManager.PERMISSION_GRANTED) {
                Log.e(TAG, "Missing permission: $perm")
                return false
            }
        }
        return true
    }

    fun startMeshNode(nodeId: String): Boolean {
        val encryptedNodeId = cryptoManager?.encryptData(nodeId.toByteArray())?.let { android.util.Base64.encodeToString(it, android.util.Base64.NO_WRAP) } ?: nodeId
        return if (nativeLoaded) {
            startMeshNodeNative(encryptedNodeId)
        } else {
            simulateStartMeshNode(encryptedNodeId)
        }
    }

    fun sendDataToPeer(peerId: String, data: ByteArray): Boolean {
        val key = cryptoManager?.deriveDeviceKey() ?: return false
        val iv = ByteArray(12).also { SecureRandom().nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(data)
        val combined = iv + encrypted
        return if (nativeLoaded) {
            sendDataToPeerNative(peerId, combined)
        } else {
            simulateSendDataToPeer(peerId, combined)
        }
    }

    fun receiveDataFromPeers(): ByteArray? {
        val received = if (nativeLoaded) {
            receiveDataFromPeersNative()
        } else {
            simulateReceiveDataFromPeers()
        }
        if (received == null) return null
        return try {
            val iv = received.sliceArray(0..11)
            val ct = received.sliceArray(12 until received.size)
            val key = cryptoManager?.deriveDeviceKey() ?: return null
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
            cipher.doFinal(ct)
        } catch (e: Exception) {
            Log.e(TAG, "Decryption failed: ${e.message}")
            null
        }
    }

    fun stopMeshNode(): Boolean {
        return if (nativeLoaded) {
            stopMeshNodeNative()
        } else {
            simulateStopMeshNode()
        }
    }

    // Fallback simulation methods for devices without native library
    private fun simulateStartMeshNode(nodeId: String): Boolean {
        Log.d(TAG, "Simulated start mesh node: $nodeId")
        return true
    }

    private fun simulateSendDataToPeer(peerId: String, data: ByteArray): Boolean {
        Log.d(TAG, "Simulated send data to peer: $peerId, size: ${data.size}")
        return true
    }

    private fun simulateReceiveDataFromPeers(): ByteArray? {
        Log.d(TAG, "Simulated receive data from peers")
        return null
    }

    private fun simulateStopMeshNode(): Boolean {
        Log.d(TAG, "Simulated stop mesh node")
        return true
    }
}