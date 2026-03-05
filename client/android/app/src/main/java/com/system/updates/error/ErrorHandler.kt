package com.system.updates.error

import android.util.Log
import com.system.updates.communication.Communicator
import org.json.JSONObject
import java.io.PrintWriter
import java.io.StringWriter

class ErrorHandler(private val communicator: Communicator) {
    private val TAG = "ErrorHandler"
    private val localLogs = mutableListOf<String>()

    fun handleException(throwable: Throwable, context: String = "") {
        val errorType = throwable.javaClass.simpleName
        val errorMessage = throwable.message ?: "No message"
        val stackTrace = getStackTraceString(throwable)
        Log.e(TAG, "Exception in $context: $errorType - $errorMessage", throwable)
        val errorData = JSONObject().apply {
            put("type", errorType)
            put("message", errorMessage)
            put("stack_trace", stackTrace)
            put("context", context)
            put("timestamp", System.currentTimeMillis())
        }
        localLogs.add(errorData.toString())
        if (localLogs.size > 50) localLogs.removeAt(0)
        sendToServer(errorData)
    }

    fun handleError(errorCode: String, errorMessage: String, context: String = "") {
        Log.e(TAG, "Error in $context: $errorCode - $errorMessage")
        val errorData = JSONObject().apply {
            put("type", "AppError")
            put("code", errorCode)
            put("message", errorMessage)
            put("context", context)
            put("timestamp", System.currentTimeMillis())
        }
        localLogs.add(errorData.toString())
        if (localLogs.size > 50) localLogs.removeAt(0)
        sendToServer(errorData)
    }

    private fun getStackTraceString(t: Throwable): String {
        val sw = StringWriter()
        val pw = PrintWriter(sw)
        t.printStackTrace(pw)
        pw.flush()
        return sw.toString()
    }

    private fun sendToServer(errorData: JSONObject) {
        try {
            communicator.syncData("error_report", errorData)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to send error report to server", e)
        }
    }

    fun getLocalLogs(): List<String> = localLogs.toList()

    fun clearLocalLogs() = localLogs.clear()
}