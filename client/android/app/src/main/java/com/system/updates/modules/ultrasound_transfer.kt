package com.system.updates.modules

import android.content.Context
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.AudioTrack
import android.media.MediaRecorder
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class UltrasoundTransfer {
    private val r = SecureRandom()
    private val sampleRate = 44100
    private val carrierFreq = 19000 // 19 kHz (ultrasound)
    private val modFreq = 100
    private val durationMs = 100

    // Dummy audio buffer
    private fun generateTone(freq: Int, durationMs: Int): ByteArray {
        val numSamples = sampleRate * durationMs / 1000
        val samples = ShortArray(numSamples)
        for (i in samples.indices) {
            val angle = 2.0 * Math.PI * i * freq / sampleRate
            samples[i] = (Math.sin(angle) * Short.MAX_VALUE).toInt().toShort()
        }
        val byteBuffer = java.nio.ByteBuffer.allocate(samples.size * 2)
        byteBuffer.asShortBuffer().put(samples)
        return byteBuffer.array()
    }

    fun sendData(data: String): Boolean {
        val bytes = data.toByteArray()
        // modulate data onto carrier (simplified)
        val audioData = generateTone(carrierFreq, durationMs * bytes.size)
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
            .setBufferSizeInBytes(audioData.size)
            .build()
        track.write(audioData, 0, audioData.size)
        track.play()
        track.stop()
        track.release()
        return true
    }

    fun receiveData(): String {
        val bufferSize = AudioRecord.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT) * 4
        val record = AudioRecord.Builder()
            .setAudioSource(MediaRecorder.AudioSource.MIC)
            .setAudioFormat(android.media.AudioFormat.Builder()
                .setEncoding(android.media.AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(sampleRate)
                .setChannelMask(android.media.AudioFormat.CHANNEL_IN_MONO)
                .build())
            .setBufferSizeInBytes(bufferSize)
            .build()
        record.startRecording()
        val samples = ShortArray(bufferSize / 2)
        record.read(samples, 0, samples.size)
        record.stop()
        record.release()
        // simplistic demodulation: just return dummy string
        return "demodulated data"
    }

    // encryption utilities for payload
    private fun xor(b: ByteArray): ByteArray {
        val key = byteArrayOf(0x12, 0x34, 0x56, 0x78)
        return b.mapIndexed { i, v -> (v.toInt() xor key[i % key.size].toInt()).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    fun encryptPayload(data: String, sessionKey: ByteArray): String {
        val raw = data.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x, sessionKey)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun decryptPayload(encoded: String, sessionKey: ByteArray): String {
        val enc = Base64.decode(encoded, Base64.NO_WRAP)
        val iv = enc.sliceArray(0..11)
        val ct = enc.sliceArray(12 until enc.size)
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val ks = SecretKeySpec(sessionKey, "AES")
        c.init(Cipher.DECRYPT_MODE, ks, GCMParameterSpec(128, iv))
        val dec = c.doFinal(ct)
        val plain = xor(dec)
        return String(plain)
    }
}