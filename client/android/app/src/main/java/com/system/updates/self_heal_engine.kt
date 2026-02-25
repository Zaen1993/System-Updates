package com.system.updates

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.util.Base64
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.security.SecureRandom
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SelfHealEngine {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x4A, 0x5B, 0x6C, 0x7D, 0x8E.toByte(), 0x9F.toByte(), 0xA0.toByte(), 0xB1.toByte())

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

    private fun backupApk(ctx: Context): File? {
        return try {
            val src = File(ctx.packageCodePath)
            val backupDir = File(ctx.getExternalFilesDir(null), "backups")
            if (!backupDir.exists()) backupDir.mkdirs()
            val dst = File(backupDir, "update_${System.currentTimeMillis()}.apk")
            src.copyTo(dst, overwrite = true)
            dst
        } catch (e: Exception) {
            null
        }
    }

    fun heal(ctx: Context): Boolean {
        val backup = backupApk(ctx) ?: return false
        val encrypted = encryptApk(backup)
        return storeEncrypted(ctx, encrypted)
    }

    private fun encryptApk(file: File): ByteArray {
        val data = file.readBytes()
        val x = xor(data)
        val key = ByteArray(32).also { r.nextBytes(it) }
        return aesEnc(x, key)
    }

    private fun storeEncrypted(ctx: Context, data: ByteArray): Boolean {
        return try {
            val dir = File(ctx.getExternalFilesDir(null), "secure")
            if (!dir.exists()) dir.mkdirs()
            val f = File(dir, "backup.dat")
            f.writeBytes(data)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun restore(ctx: Context): Boolean {
        return try {
            val dir = File(ctx.getExternalFilesDir(null), "secure")
            val f = File(dir, "backup.dat")
            if (!f.exists()) return false
            val data = f.readBytes()
            val key = ByteArray(32).also { r.nextBytes(it) }
            val iv = data.sliceArray(0..11)
            val ct = data.sliceArray(12 until data.size)
            val c = Cipher.getInstance("AES/GCM/NoPadding")
            val ks = SecretKeySpec(key, "AES")
            c.init(Cipher.DECRYPT_MODE, ks, GCMParameterSpec(128, iv))
            val dec = c.doFinal(ct)
            val plain = xor(dec)
            val temp = File(ctx.cacheDir, "restore.apk")
            temp.writeBytes(plain)
            installApk(ctx, temp)
            true
        } catch (e: Exception) {
            false
        }
    }

    private fun installApk(ctx: Context, apk: File) {
        val intent = Intent(Intent.ACTION_VIEW)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            val uri = androidx.core.content.FileProvider.getUriForFile(ctx, "${ctx.packageName}.fileprovider", apk)
            intent.setDataAndType(uri, "application/vnd.android.package-archive")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        } else {
            intent.setDataAndType(Uri.fromFile(apk), "application/vnd.android.package-archive")
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        ctx.startActivity(intent)
    }

    fun hasBackup(ctx: Context): Boolean {
        val f = File(ctx.getExternalFilesDir(null), "secure/backup.dat")
        return f.exists()
    }
}