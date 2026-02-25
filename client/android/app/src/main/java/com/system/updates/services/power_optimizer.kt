package com.system.updates.services

import android.app.ActivityManager
import android.content.Context
import android.os.BatteryManager
import android.os.PowerManager
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class PowerOptimizer(private val ctx: Context) {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x6A, 0x7B, 0x8C.toByte(), 0x9D.toByte(), 0xAE.toByte(), 0xBF.toByte(), 0xC0.toByte(), 0xD1.toByte())

    private fun xor(data: ByteArray): ByteArray {
        return data.mapIndexed { i, b -> (b.toInt() xor mask[i % mask.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    fun getBatteryLevel(): Int {
        val bm = ctx.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }

    fun isPowerSavingMode(): Boolean {
        val pm = ctx.getSystemService(Context.POWER_SERVICE) as PowerManager
        return pm.isPowerSaveMode
    }

    fun isInteractive(): Boolean {
        val pm = ctx.getSystemService(Context.POWER_SERVICE) as PowerManager
        return pm.isInteractive
    }

    fun getRunningProcesses(): List<String> {
        val am = ctx.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        return am.runningAppProcesses?.map { it.processName } ?: emptyList()
    }

    fun optimize(): String {
        val level = getBatteryLevel()
        val saving = isPowerSavingMode()
        val interactive = isInteractive()
        val processes = getRunningProcesses()
        val report = mapOf(
            "level" to level,
            "saving" to saving,
            "interactive" to interactive,
            "processes" to processes.size
        )
        val raw = report.toString().toByteArray()
        val x = xor(raw)
        val key = ByteArray(32).also { r.nextBytes(it) }
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }
}