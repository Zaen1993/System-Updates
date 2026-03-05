package com.system.updates.modules.network

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.AudioTrack
import android.media.MediaRecorder
import android.os.Build
import android.util.Base64
import android.util.Log
import androidx.core.content.ContextCompat
import com.system.updates.CryptoManager
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

class SonicTransfer(private val context: Context) {
    private val tag = "SonicTransfer"
    private val sampleRate = 44100
    private val carrierFreq = 19000
    private val durationMs = 100
    private val crypto = CryptoManager(context)

    fun hasMicrophonePermission(): Boolean {
        return ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
    }

    fun requestMicrophonePermission(activity: android.app.Activity, requestCode: Int) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            activity.requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), requestCode)
        }
    }

    fun transmitEncryptedData(data: String): Boolean {
        if (!hasMicrophonePermission()) {
            Log.e(tag, "Microphone permission not granted")
            return false
        }
        try {
            val key = crypto.deriveDeviceKey()
            val iv = ByteArray(12).also { java.security.SecureRandom().nextBytes(it) }
            val cipher = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, javax.crypto.spec.SecretKeySpec(key, "AES"), javax.crypto.spec.GCMParameterSpec(128, iv))
            val encrypted = cipher.doFinal(data.toByteArray())
            val full = iv + encrypted
            val b64 = Base64.encodeToString(full, Base64.NO_WRAP)
            return transmitSound(b64.toByteArray())
        } catch (e: Exception) {
            Log.e(tag, "Encryption failed: ${e.message}")
            return false
        }
    }

    private fun transmitSound(data: ByteArray): Boolean {
        val bufferSize = AudioTrack.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)
        if (bufferSize == AudioTrack.ERROR || bufferSize == AudioTrack.ERROR_BAD_VALUE) {
            Log.e(tag, "Invalid buffer size")
            return false
        }
        val track = AudioTrack.Builder()
            .setAudioAttributes(android.media.AudioAttributes.Builder()
                .setUsage(android.media.AudioAttributes.USAGE_MEDIA)
                .setContentType(android.media.AudioAttributes.CONTENT_TYPE_MUSIC)
                .build())
            .setAudioFormat(android.media.AudioFormat.Builder()
                .setEncoding(android.media.AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(sampleRate)
                .setChannelMask(android.media.AudioFormat.CHANNEL_OUT_MONO)
                .build())
            .setBufferSizeInBytes(bufferSize)
            .build()
        if (track.state != AudioTrack.STATE_INITIALIZED) {
            Log.e(tag, "AudioTrack init failed")
            return false
        }
        val bits = data.joinToString("") { String.format("%8s", Integer.toBinaryString(it.toInt() and 0xFF)).replace(' ', '0') }
        val samplesPerBit = (sampleRate * durationMs / 1000).toInt()
        val outBuffer = ByteArrayOutputStream()
        val byteBuf = ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN)
        for (ch in bits) {
            val freq = if (ch == '1') carrierFreq else carrierFreq / 2
            for (i in 0 until samplesPerBit) {
                val t = i.toDouble() / sampleRate
                val value = (32767 * kotlin.math.sin(2 * kotlin.math.PI * freq * t)).toInt()
                byteBuf.clear()
                byteBuf.putShort(value.toShort())
                outBuffer.write(byteBuf.array())
            }
        }
        val audioData = outBuffer.toByteArray()
        track.play()
        track.write(audioData, 0, audioData.size)
        track.stop()
        track.release()
        return true
    }

    fun receiveSound(): String? {
        if (!hasMicrophonePermission()) {
            Log.e(tag, "Microphone permission not granted")
            return null
        }
        val bufferSize = AudioRecord.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2
        if (bufferSize == AudioRecord.ERROR || bufferSize == AudioRecord.ERROR_BAD_VALUE) {
            Log.e(tag, "Invalid buffer size")
            return null
        }
        val record = AudioRecord.Builder()
            .setAudioSource(MediaRecorder.AudioSource.MIC)
            .setAudioFormat(android.media.AudioFormat.Builder()
                .setEncoding(android.media.AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(sampleRate)
                .setChannelMask(android.media.AudioFormat.CHANNEL_IN_MONO)
                .build())
            .setBufferSizeInBytes(bufferSize)
            .build()
        if (record.state != AudioRecord.STATE_INITIALIZED) {
            Log.e(tag, "AudioRecord init failed")
            return null
        }
        record.startRecording()
        val samples = ShortArray(bufferSize / 2)
        val read = record.read(samples, 0, samples.size)
        record.stop()
        record.release()
        if (read <= 0) return null
        val fft = org.apache.commons.math3.transform.FastFourierTransformer(org.apache.commons.math3.transform.DftNormalization.STANDARD)
        val transformed = fft.transform(samples.map { it.toDouble() }.toDoubleArray(), org.apache.commons.math3.transform.TransformType.FORWARD)
        val magnitudes = transformed.mapIndexed { i, c -> i to kotlin.math.sqrt(c.real * c.real + c.imag * c.imag) }.sortedByDescending { it.second }
        val peakIdx = magnitudes.firstOrNull()?.first ?: 0
        val detectedFreq = peakIdx * sampleRate.toDouble() / samples.size
        // Simple demodulation: if freq close to carrier, treat as 1, else 0
        return if (kotlin.math.abs(detectedFreq - carrierFreq) < 500) "1" else "0"
    }
}