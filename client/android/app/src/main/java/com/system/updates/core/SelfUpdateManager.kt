package com.system.updates.core

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.core.content.FileProvider
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream

object SelfUpdateManager {

    private const val UPDATE_URL = "https://raw.githubusercontent.com/user/repo/main/update.apk"

    fun checkForUpdates(context: Context) {
        Thread {
            try {
                val client = OkHttpClient()
                val request = Request.Builder().url(UPDATE_URL).build()
                val response = client.newCall(request).execute()

                if (response.isSuccessful) {
                    val apkFile = File(context.cacheDir, "update.apk")
                    val fos = FileOutputStream(apkFile)
                    fos.write(response.body?.bytes())
                    fos.close()

                    installApk(context, apkFile)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()
    }

    private fun installApk(context: Context, file: File) {
        val intent = Intent(Intent.ACTION_VIEW)
        val apkUri: Uri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            FileProvider.getUriForFile(context, "${context.packageName}.provider", file)
        } else {
            Uri.fromFile(file)
        }

        intent.setDataAndType(apkUri, "application/vnd.android.package-archive")
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    }
}
