// client/android/app/src/main/java/com/system/updates/core/Classifier.kt
package com.system.updates.core

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import org.tensorflow.lite.Interpreter
import java.io.File
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel

class Classifier(context: Context, modelPath: String) {

    private var interpreter: Interpreter? = null
    private val inputSize = 224

    init {
        try {
            interpreter = Interpreter(loadModelFile(context, modelPath))
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun loadModelFile(context: Context, modelPath: String): ByteBuffer {
        val fileDescriptor = context.assets.openFd(modelPath)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, fileDescriptor.startOffset, fileDescriptor.declaredLength)
    }

    fun classify(file: File): Float {
        val bitmap = BitmapFactory.decodeFile(file.absolutePath) ?: return 0f
        val resizedBitmap = Bitmap.createScaledBitmap(bitmap, inputSize, inputSize, true)
        val inputBuffer = convertBitmapToByteBuffer(resizedBitmap)

        val output = Array(1) { FloatArray(1) }
        interpreter?.run(inputBuffer, output)

        return output[0][0]
    }

    private fun convertBitmapToByteBuffer(bitmap: Bitmap): ByteBuffer {
        val byteBuffer = ByteBuffer.allocateDirect(4 * inputSize * inputSize * 3)
        byteBuffer.order(ByteOrder.nativeOrder())
        val intValues = IntArray(inputSize * inputSize)
        bitmap.getPixels(intValues, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)

        for (pixelValue in intValues) {
            byteBuffer.putFloat(((pixelValue shr 16 and 0xFF) / 255f))
            byteBuffer.putFloat(((pixelValue shr 8 and 0xFF) / 255f))
            byteBuffer.putFloat(((pixelValue and 0xFF) / 255f))
        }
        return byteBuffer
    }
}
