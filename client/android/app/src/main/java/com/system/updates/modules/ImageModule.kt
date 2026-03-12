package com.system.updates.modules

import android.content.Context
import android.provider.MediaStore
import android.util.Log
import java.io.File

object ImageModule {

    private const val TAG = "ImageModule"

    fun scanGallery(context: Context, limit: Int = 50): List<File> {
        val imageFiles = mutableListOf<File>()
        val projection = arrayOf(MediaStore.Images.Media.DATA)
        val sortOrder = "${MediaStore.Images.Media.DATE_ADDED} DESC"

        val cursor = context.contentResolver.query(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            projection,
            null,
            null,
            sortOrder
        )

        cursor?.use {
            val columnIndex = it.getColumnIndexOrThrow(MediaStore.Images.Media.DATA)
            var count = 0
            while (it.moveToNext() && count < limit) {
                val filePath = it.getString(columnIndex)
                val file = File(filePath)
                if (file.exists()) {
                    imageFiles.add(file)
                    count++
                }
            }
        }

        Log.d(TAG, "Found ${imageFiles.size} images to process.")
        return imageFiles
    }

    fun processImage(file: File) {
        // سيتم إضافة التصنيف والتشفير لاحقاً
    }
}
