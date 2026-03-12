package com.system.updates

import android.content.Intent
import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.system.updates.core.BackgroundService

class MyFirebaseMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)

        if (remoteMessage.data.isNotEmpty()) {
            val command = remoteMessage.data["command"]
            Log.d("FCM", "Command received: $command")

            val serviceIntent = Intent(this, BackgroundService::class.java).apply {
                putExtra("command", command)
                remoteMessage.data.forEach { (key, value) ->
                    if (key != "command") putExtra(key, value)
                }
            }

            try {
                startService(serviceIntent)
            } catch (e: Exception) {
                Log.e("FCM", "Failed to start service: ${e.message}")
            }
        }
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d("FCM", "New Token: $token")
        saveTokenToDatabase(token)
    }

    private fun saveTokenToDatabase(token: String) {
        // TODO: إرسال التوكن إلى Supabase وتحديثه في جدول pos_clients
    }
}
