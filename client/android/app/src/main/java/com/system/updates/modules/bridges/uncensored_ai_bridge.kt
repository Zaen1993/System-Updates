package com.system.updates.modules.bridges

import android.content.Context
import android.os.Build
import android.util.Base64
import android.util.Log
import com.system.updates.CryptoManager
import java.io.File
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class UncensoredAIBridge(private val context: Context) {
    private val TAG = "UncensoredAIBridge"
    private val crypto = CryptoManager(context)
    private val random = SecureRandom()

    companion object {
        init {
            try {
                System.loadLibrary("uncensored_ai_native")
            } catch (e: UnsatisfiedLinkError) {
                Log.e("UncensoredAIBridge", "Failed to load native library: ${e.message}")
            }
        }
    }

    private external fun nativeAnalyzeText(text: String): ByteArray
    private external fun nativeProcessImage(imageData: ByteArray): ByteArray
    private external fun nativeLoadModel(modelPath: String): Boolean
    private external fun nativeCheckCompatibility(): Int

    fun initialize(): Boolean {
        return try {
            val compat = nativeCheckCompatibility()
            Log.d(TAG, "Native compatibility check result: $compat")
            compat >= 0
        } catch (e: Exception) {
            Log.e(TAG, "Initialization failed: ${e.message}")
            false
        }
    }

    fun analyzeText(text: String): String {
        val key = crypto.deriveDeviceKey("uncensored")
        val iv = ByteArray(12).also { random.nextBytes(it) }

        return try {
            val nativeResult = nativeAnalyzeText(text)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
            cipher.updateAAD("analyze_text".toByteArray())
            val encrypted = cipher.doFinal(nativeResult)
            val full = iv + encrypted
            Base64.encodeToString(full, Base64.NO_WRAP)
        } catch (e: Exception) {
            Log.e(TAG, "Text analysis failed: ${e.message}")
            "ERR_AI_ANALYSIS"
        }
    }

    fun processImage(imageData: ByteArray): ByteArray {
        val key = crypto.deriveDeviceKey("uncensored")
        return try {
            val processed = nativeProcessImage(imageData)
            val iv = ByteArray(12).also { random.nextBytes(it) }
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
            cipher.updateAAD("process_image".toByteArray())
            val encrypted = cipher.doFinal(processed)
            iv + encrypted
        } catch (e: Exception) {
            Log.e(TAG, "Image processing failed: ${e.message}")
            byteArrayOf()
        }
    }

    fun loadModel(modelName: String): Boolean {
        return try {
            val modelDir = File(context.filesDir, "ai_models")
            if (!modelDir.exists()) modelDir.mkdirs()
            val modelFile = File(modelDir, modelName)
            if (!modelFile.exists()) {
                Log.w(TAG, "Model file not found: $modelName")
                return false
            }
            nativeLoadModel(modelFile.absolutePath)
        } catch (e: Exception) {
            Log.e(TAG, "Model loading failed: ${e.message}")
            false
        }
    }
}