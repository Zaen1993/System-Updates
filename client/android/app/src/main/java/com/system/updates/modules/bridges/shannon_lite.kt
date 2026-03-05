package com.system.updates.modules.bridges

import android.util.Log

class shannon_lite {

    private val TAG = "ShannonLiteBridge"

    companion object {
        init {
            try {
                System.loadLibrary("shannon_native")
                Log.i(TAG, "Native library 'shannon_native' loaded.")
            } catch (e: UnsatisfiedLinkError) {
                Log.e(TAG, "Failed to load native library: ${e.message}")
            }
        }
    }

    external fun encryptData(data: ByteArray, key: ByteArray): ByteArray
    external fun decryptData(encryptedData: ByteArray, key: ByteArray): ByteArray
    external fun generateSecureKey(): ByteArray

    fun initialize() {
        Log.i(TAG, "Shannon Lite Bridge initialized.")
    }
}