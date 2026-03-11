# ==================== config.py ====================
import os

class Config:
    MASTER_PASS = os.getenv("MASTER_PASS")
    _raw_tokens = os.getenv("TELEGRAM_BOT_TOKENS", "")
    BOT_TOKENS = [t.strip() for t in _raw_tokens.split(",") if t.strip()]

    SUPABASE = [
        {"url": os.getenv("SUPABASE_URL_1"), "key": os.getenv("SUPABASE_KEY_1")},
        {"url": os.getenv("SUPABASE_URL_2"), "key": os.getenv("SUPABASE_KEY_2")},
        {"url": os.getenv("SUPABASE_URL_3"), "key": os.getenv("SUPABASE_KEY_3")},
        {"url": os.getenv("SUPABASE_URL_4"), "key": os.getenv("SUPABASE_KEY_4")}
    ]

    CHATS = {
        "CONTROL": int(os.getenv("CHANNEL_ID_CONTROL", "0")),
        "DATA": int(os.getenv("CHANNEL_ID_DATA", "0"))
    }
