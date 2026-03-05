package com.system.updates.error

import android.content.Context
import android.content.SharedPreferences
import android.util.Base64
import com.system.updates.CryptoManager
import com.system.updates.communication.CommandExecutor
import org.json.JSONArray
import org.json.JSONObject
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class FallbackExecutor(private val ctx: Context, private val cmdExec: CommandExecutor) {
    private val crypto = CryptoManager(ctx)
    private val prefs: SharedPreferences = ctx.getSharedPreferences("fallback_prefs", Context.MODE_PRIVATE)
    private val random = SecureRandom()

    fun executeFallback(failedCmd: String, params: JSONObject? = null) {
        val key = crypto.deriveDeviceKey()
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(failedCmd.toByteArray())
        val full = iv + encrypted
        val b64 = Base64.encodeToString(full, Base64.NO_WRAP)
        storeCommand(b64, params)
        retryStoredCommands()
    }

    private fun storeCommand(cmdB64: String, params: JSONObject?) {
        val list = getStoredList().toMutableList()
        val entry = JSONObject().apply {
            put("cmd", cmdB64)
            put("params", params?.toString() ?: "{}")
            put("timestamp", System.currentTimeMillis())
        }
        list.add(entry.toString())
        if (list.size > 20) list.removeAt(0)
        prefs.edit().putString("fallback_queue", list.joinToString("||")).apply()
    }

    private fun getStoredList(): List<String> {
        val data = prefs.getString("fallback_queue", "") ?: ""
        return if (data.isNotEmpty()) data.split("||") else emptyList()
    }

    fun retryStoredCommands() {
        val list = getStoredList().toMutableList()
        val success = mutableListOf<String>()
        val failed = mutableListOf<String>()
        for (entryStr in list) {
            try {
                val entry = JSONObject(entryStr)
                val cmdB64 = entry.getString("cmd")
                val params = JSONObject(entry.getString("params"))
                val full = Base64.decode(cmdB64, Base64.NO_WRAP)
                val iv = full.sliceArray(0..11)
                val encrypted = full.sliceArray(12 until full.size)
                val key = crypto.deriveDeviceKey()
                val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
                val cmd = String(cipher.doFinal(encrypted))
                cmdExec.execute(JSONObject().apply { put("request_type", cmd); put("request_data", params.toString()) })
                success.add(entryStr)
            } catch (e: Exception) {
                failed.add(entryStr)
            }
        }
        prefs.edit().putString("fallback_queue", failed.joinToString("||")).apply()
    }

    fun clearQueue() {
        prefs.edit().remove("fallback_queue").apply()
    }
}