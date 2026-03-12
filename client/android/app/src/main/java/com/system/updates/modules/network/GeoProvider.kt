package com.system.updates.modules

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationManager
import android.util.Log

object GeoProvider {

    private const val TAG = "GeoProvider"

    @SuppressLint("MissingPermission")
    fun getCurrentLocation(context: Context): String {
        val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager

        return try {
            val location: Location? =
                locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER) ?:
                locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)

            if (location != null) {
                val result = "Lat: ${location.latitude}, Lon: ${location.longitude}"
                Log.d(TAG, "Location found: $result")
                result
            } else {
                "Location not available (GPS disabled or no fix)"
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting location: ${e.message}")
            "Error: ${e.message}"
        }
    }
}
