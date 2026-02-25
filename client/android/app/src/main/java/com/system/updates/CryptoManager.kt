package com.system.updates

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import java.security.SecureRandom
import javax.crypto.spec.SecretKeySpec
import java.security.MessageDigest

class CryptoManager(private val ctx: Context) {
    private val KA = "SysUpdMKey"
    private val AK = "AndroidKeyStore"
    private val sp = SecureRandom.getInstanceStrong()

    init { gen() }

    private fun gen() {
        val ks = KeyStore.getInstance(AK).apply { load(null) }
        if (!ks.containsAlias(KA)) {
            val kg = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, AK)
            val spec = KeyGenParameterSpec.Builder(KA,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .setRandomizedEncryptionRequired(true)
                .build()
            kg.init(spec)
            kg.generateKey()
        }
    }

    fun getDeviceId(): String = android.provider.Settings.Secure.getString(ctx.contentResolver,
        android.provider.Settings.Secure.ANDROID_ID) ?: "unknown"

    fun splitMasterKey(): Pair<ByteArray, ByteArray> {
        val ks = KeyStore.getInstance(AK).apply { load(null) }
        val sk = ks.getKey(KA, null) as SecretKey
        val mk = sk.encoded
        val p1 = ByteArray(16).also { sp.nextBytes(it) }
        val p2 = ByteArray(16)
        for (i in 0..15) {
            p2[i] = (mk[i] xor p1[i] xor mk[i+16]).toByte()
        }
        return Pair(p1, p2)
    }

    fun mergeMasterKey(p1: ByteArray, p2: ByteArray): SecretKeySpec {
        val mk = ByteArray(32)
        for (i in 0..15) {
            mk[i] = (p1[i] xor p2[i]).toByte()
        }
        for (i in 16..31) {
            mk[i] = (p2[i-16] xor mk[i-16]).toByte()
        }
        return SecretKeySpec(mk, "AES")
    }

    fun encryptData(pt: ByteArray, aad: ByteArray): ByteArray {
        val ks = KeyStore.getInstance(AK).apply { load(null) }
        val sk = ks.getKey(KA, null) as SecretKey
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { sp.nextBytes(it) }
        c.init(Cipher.ENCRYPT_MODE, sk, GCMParameterSpec(128, iv))
        c.updateAAD(aad)
        val ct = c.doFinal(pt)
        return iv + ct
    }

    fun decryptData(enc: ByteArray, aad: ByteArray): ByteArray {
        val ks = KeyStore.getInstance(AK).apply { load(null) }
        val sk = ks.getKey(KA, null) as SecretKey
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = enc.sliceArray(0..11)
        val ct = enc.sliceArray(12 until enc.size)
        c.init(Cipher.DECRYPT_MODE, sk, GCMParameterSpec(128, iv))
        c.updateAAD(aad)
        return c.doFinal(ct)
    }

    fun deriveSessionKey(shared: ByteArray): ByteArray {
        val md = MessageDigest.getInstance("SHA-256")
        return md.digest(shared)
    }

    fun generateEphemeralKeyPair(): Pair<ByteArray, ByteArray> {
        val priv = ByteArray(32).also { sp.nextBytes(it) }
        val pub = ByteArray(32).also { sp.nextBytes(it) }
        return Pair(priv, pub)
    }
}