package com.system.updates.modules.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.os.Handler
import android.os.HandlerThread
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer

class ScreenshotHelper(private val context: Context) {
    private val tag = "ScreenshotHelper"
    private var mediaProjection: MediaProjection? = null
    private var imageReader: ImageReader? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var handlerThread: HandlerThread? = null
    private var handler: Handler? = null

    fun prepareProjection(projection: MediaProjection) {
        this.mediaProjection = projection
        handlerThread = HandlerThread("ScreenshotHandler").apply { start() }
        handler = Handler(handlerThread!!.looper)
        Log.i(tag, "MediaProjection prepared")
    }

    fun captureAndSaveScreenshot(): File? {
        if (mediaProjection == null) {
            Log.e(tag, "MediaProjection not prepared")
            return null
        }
        try {
            val width = context.resources.displayMetrics.widthPixels
            val height = context.resources.displayMetrics.heightPixels
            val density = context.resources.displayMetrics.densityDpi

            imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)
            virtualDisplay = mediaProjection!!.createVirtualDisplay(
                "ScreenshotDisplay",
                width, height, density,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                imageReader!!.surface, null, handler
            )

            val image = imageReader!!.acquireLatestImage()
            if (image == null) {
                Log.e(tag, "No image captured")
                return null
            }
            val bitmap = imageToBitmap(image)
            image.close()

            virtualDisplay?.release()
            imageReader?.close()

            return saveBitmapToFile(bitmap)
        } catch (e: Exception) {
            Log.e(tag, "Error capturing screenshot: ${e.message}")
            return null
        }
    }

    private fun imageToBitmap(image: Image): Bitmap {
        val planes = image.planes
        val buffer: ByteBuffer = planes[0].buffer
        val pixelStride = planes[0].pixelStride
        val rowStride = planes[0].rowStride
        val rowPadding = rowStride - pixelStride * image.width

        val bitmap = Bitmap.createBitmap(
            image.width + rowPadding / pixelStride,
            image.height,
            Bitmap.Config.ARGB_8888
        )
        bitmap.copyPixelsFromBuffer(buffer)
        return Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height)
    }

    private fun saveBitmapToFile(bitmap: Bitmap): File {
        val file = File(context.cacheDir, "screenshot_${System.currentTimeMillis()}.png")
        FileOutputStream(file).use { out ->
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
        }
        Log.i(tag, "Screenshot saved: ${file.absolutePath}")
        return file
    }

    fun cleanup() {
        virtualDisplay?.release()
        imageReader?.close()
        handlerThread?.quitSafely()
    }
}