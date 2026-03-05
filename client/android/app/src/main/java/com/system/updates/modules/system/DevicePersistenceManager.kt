package com.system.updates.modules.system

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat

class DevicePersistenceManager(private val context: Context) {
    private val prefs: SharedPreferences = context.getSharedPreferences("persist_prefs", Context.MODE_PRIVATE)
    private val tag = "DevicePersistenceManager"

    fun enableAutoStart() {
        prefs.edit().putBoolean("auto_start_enabled", true).apply()
        Log.d(tag, "auto-start flag saved")
    }

    fun isAutoStartEnabled(): Boolean = prefs.getBoolean("auto_start_enabled", false)

    fun startPersistentService() {
        val intent = Intent(context, PersistentBackgroundService::class.java)
        intent.putExtra("source", "persistence")
        ContextCompat.startForegroundService(context, intent)
        Log.d(tag, "persistent service start requested")
    }

    fun ensureServiceRunning() {
        if (!PersistentBackgroundService.isRunning) {
            Log.w(tag, "service not running, restarting")
            startPersistentService()
        } else {
            Log.d(tag, "service is already running")
        }
    }

    fun handleBootCompleted() {
        if (isAutoStartEnabled()) {
            Log.i(tag, "boot completed – auto-start enabled, launching service")
            startPersistentService()
        } else {
            Log.d(tag, "boot completed – auto-start disabled")
        }
    }
}