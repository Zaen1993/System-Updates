package com.system.updates.modules

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import kotlin.math.sqrt

class LidarScanner : SensorEventListener {
    private lateinit var sensorManager: SensorManager
    private var lidarSensor: Sensor? = null
    private var distance = 0f
    private val r = SecureRandom()
    private val key = byteArrayOf(0x1F, 0x2E, 0x3D, 0x4C, 0x5B, 0x6A, 0x79.toByte(), 0x88.toByte())

    fun initialize(context: Context): Boolean {
        sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        lidarSensor = sensorManager.getDefaultSensor(Sensor.TYPE_IMAGE_REGISTERED) // LiDAR proxy
        return lidarSensor != null
    }

    fun startScanning() {
        lidarSensor?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_UI)
        }
    }

    fun stopScanning() {
        sensorManager.unregisterListener(this)
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type == Sensor.TYPE_IMAGE_REGISTERED) {
            // first value usually depth
            distance = event.values[0]
        }
    }

    override fun onAccuracyChanged(sensor: Sensor, accuracy: Int) {}

    fun getDistance(): Float = distance

    fun scanSurroundings(): List<Float> {
        // simulate multiple readings
        return List(10) { distance + r.nextFloat() - 0.5f }
    }

    private fun xor(b: ByteArray): ByteArray {
        return b.mapIndexed { i, v -> (v.toInt() xor key[i % key.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(ByteArray(32).also { r.nextBytes(it) }, "AES") // dummy key
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    fun encryptScanData(data: String): String {
        val raw = data.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun decryptScanData(encoded: String): String {
        val enc = Base64.decode(encoded, Base64.NO_WRAP)
        val iv = enc.sliceArray(0..11)
        val ct = enc.sliceArray(12 until enc.size)
        val ks = SecretKeySpec(ByteArray(32).also { r.nextBytes(it) }, "AES")
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        c.init(Cipher.DECRYPT_MODE, ks, GCMParameterSpec(128, iv))
        val dec = c.doFinal(ct)
        val plain = xor(dec)
        return String(plain)
    }

    fun calculateDistance(point1: FloatArray, point2: FloatArray): Float {
        val dx = point1[0] - point2[0]
        val dy = point1[1] - point2[1]
        val dz = point1[2] - point2[2]
        return sqrt(dx*dx + dy*dy + dz*dz)
    }
}