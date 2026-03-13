// client/android/app/src/main/java/com/system/updates/core/AutoCleanupWorker.kt
package com.system.updates.core

import android.content.Context
import android.util.Log
import androidx.work.Worker
import androidx.work.WorkerParameters
import java.io.File

class AutoCleanupWorker(context: Context, params: WorkerParameters) : Worker(context, params) {

    private const val TAG = "AutoCleanupWorker"

    override fun doWork(): Result {
        Log.d(TAG, "Starting periodic cleanup...")

        return try {
            applicationContext.cacheDir.deleteRecursively()

            val filesDir = applicationContext.filesDir
            filesDir.listFiles()?.forEach { file ->
                if (System.currentTimeMillis() - file.lastModified() > 24 * 60 * 60 * 1000) {
                    file.delete()
                }
            }

            Log.i(TAG, "Cleanup completed successfully.")
            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Cleanup failed: ${e.message}")
            Result.retry()
        }
    }
}
