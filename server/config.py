import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    TELEGRAM_DATA_VAULT_ID = os.getenv("TELEGRAM_DATA_VAULT_ID")
    TELEGRAM_CONTROL_CENTER_ID = os.getenv("TELEGRAM_CONTROL_CENTER_ID")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    MASTER_ENCRYPTION_KEY = os.getenv("MASTER_ENCRYPTION_KEY", "default_secret_key_change_me")
    PORT = int(os.getenv("PORT", 10000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate_config(cls):
        required_vars = {
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
            "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_DATA_VAULT_ID": cls.TELEGRAM_DATA_VAULT_ID,
            "TELEGRAM_CONTROL_CENTER_ID": cls.TELEGRAM_CONTROL_CENTER_ID
        }
        missing = [var for var, value in required_vars.items() if not value]
        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            print(error_msg)
            raise EnvironmentError(error_msg)
        print("All configurations loaded successfully from environment.")

Config.validate_config()
