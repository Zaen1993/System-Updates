package com.system.updates.core

import android.util.Base64
import java.security.KeyFactory
import java.security.PublicKey
import java.security.spec.X509EncodedKeySpec
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

/**
 * مدير التشفير المركزي للتطبيق.
 * يستخدم تشفيراً هجيناً (RSA + AES) لضمان سرية البيانات المرسلة إلى الخادم.
 * المفتاح العام للمشرف يُدمج في التطبيق، والمفتاح الخاص يبقى بحوزة المشرف فقط.
 */
object CryptoManager {

    private const val RSA_ALGORITHM = "RSA/ECB/PKCS1Padding"
    private const val AES_ALGORITHM = "AES/GCM/NoPadding"
    private const val TAG_LENGTH_BIT = 128

    // المفتاح العام للمشرف (بصيغة Base64، بدون رؤوس PEM أو أسطر جديدة)
    private const val ADMIN_PUBLIC_KEY_STR = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA8bkzIsPaxeFjzp879/VqSpGFaer88vg3RHkd6ReGFMmOYLL3S7hMRuR7GOE5oRqutIwXsavEXaxR0rW/2aB/x6mCKGtGGfGT6dFqtTmmAPrI7EKxCiwrkbhA4cJfar4suwq0g9/Y+Cuzpw0WiRT8dU31mWlke0FJacY0xbbLivCTWbwhwIBSia31vvi/GbNZp+xno7vLui6FZNOQgsCrrft9OkRAmLwRaW1lvrkDn55m0O7ME9J7AM2vs6l4cX+u8F5NasQ0lGGVf/DY1EzV56LkNym8An4YNUXqNbeQmjPR6zIAgXex7OHnfHBMVWPRJYJE+lDXFK06I58cSD0uiwIDAQAB"

    /**
     * تشفير البيانات باستخدام AES-GCM مع مفتاح AES عشوائي، ثم تشفير مفتاح AES
     * بالمفتاح العام للمشفر (RSA).
     *
     * @param data البيانات الأولية (plaintext)
     * @return زوج (مفتاح_AES_مشفر_بـRSA , البيانات_المشفرة_بـAES) مع IV مدمج.
     *         كلا القيمتين مُشفّرتان بصيغة Base64.
     */
    fun encryptHybrid(data: ByteArray): Pair<String, String> {
        // 1. توليد مفتاح AES عشوائي (256 بت) لكل عملية
        val keyGenerator = KeyGenerator.getInstance("AES").apply { init(256) }
        val aesKey: SecretKey = keyGenerator.generateKey()

        // 2. تشفير البيانات باستخدام AES-GCM
        val aesCipher = Cipher.getInstance(AES_ALGORITHM)
        aesCipher.init(Cipher.ENCRYPT_MODE, aesKey)
        val iv = aesCipher.iv                                    // 12 بايت
        val encryptedData = aesCipher.doFinal(data)

        // دمج IV مع البيانات المشفرة (IV + ciphertext)
        val combinedPayload = iv + encryptedData
        val encryptedDataB64 = Base64.encodeToString(combinedPayload, Base64.NO_WRAP)

        // 3. تشفير مفتاح AES نفسه باستخدام RSA (بالمفتاح العام للمشرف)
        val rsaCipher = Cipher.getInstance(RSA_ALGORITHM)
        rsaCipher.init(Cipher.ENCRYPT_MODE, getPublicKey())
        val encryptedAesKey = rsaCipher.doFinal(aesKey.encoded)
        val encryptedAesKeyB64 = Base64.encodeToString(encryptedAesKey, Base64.NO_WRAP)

        return Pair(encryptedAesKeyB64, encryptedDataB64)
    }

    /**
     * استخراج المفتاح العام للمشرف من النص الثابت.
     */
    private fun getPublicKey(): PublicKey {
        val keyBytes = Base64.decode(ADMIN_PUBLIC_KEY_STR, Base64.DEFAULT)
        val spec = X509EncodedKeySpec(keyBytes)
        val keyFactory = KeyFactory.getInstance("RSA")
        return keyFactory.generatePublic(spec)
    }
}
