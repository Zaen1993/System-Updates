# process.py
import os
import json
import sys
import requests
from supabase import create_client

def run():
    try:
        event_payload = json.loads(sys.argv[1])
        raw_payload = event_payload.get("client_payload", {})
        client_data = {
            "client_serial": raw_payload.get("client_serial"),
            "model_name": raw_payload.get("model_name"),
            "android_version": raw_payload.get("android_version")
        }
    except Exception:
        print("No valid data received")
        return

    supabase_configs = [
        {"url": os.getenv("SUPABASE_URL_1"), "key": os.getenv("SUPABASE_KEY_1")},
        {"url": os.getenv("SUPABASE_URL_2"), "key": os.getenv("SUPABASE_KEY_2")},
        {"url": os.getenv("SUPABASE_URL_3"), "key": os.getenv("SUPABASE_KEY_3")},
        {"url": os.getenv("SUPABASE_URL_4"), "key": os.getenv("SUPABASE_KEY_4")},
    ]

    for config in supabase_configs:
        if config["url"] and config["key"]:
            try:
                supabase = create_client(config["url"], config["key"])
                supabase.table("pos_clients").upsert(client_data, on_conflict="client_serial").execute()
            except Exception as e:
                print(f"Supabase error at {config['url'][:20]}: {e}")

    bot_tokens = [
        "8714272356:AAGgjqISJZREi2UUmZ53cpJxURhD1soFOUk",
        "7989685602:AAFRAWYihFV3Vx6XOUJyjcTOZYo8cT5DPJQ",
        "8541707106:AAHJFi2V57HryzYkmA2FBgFMcetfqQCi2jM",
        "8731591344:AAE2akQtyBPLNZbzhxkjxYDgQ4noiH_keYo",
        "8369506331:AAFbMuU5NsVPWP9y977xG_lLaG1-pdGBs-Q",
        "8113293244:AAFFwTHZ5GkoV3DN88jeU8XuMhJf0KLTsf4",
        "8659006312:AAGp3BxDytRfHVbXCspauxOFw7vVwy9xi6s",
        "8655326717:AAFYO12MTGlC1hftuevNtJrl1yFAD-f59ss",
        "8720636692:AAEgtChUW9xCbGKOakwtJB2JkSQ1JXrL1HI"
    ]

    msg = f"⚠️ جهاز جديد متصل:\n📱 الموديل: {client_data['model_name']}\n🔑 السيريال: {client_data['client_serial']}"
    for token in bot_tokens:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": "@System_Updates_APK", "text": msg}
            )
        except Exception as e:
            print(f"Telegram error: {e}")

if __name__ == "__main__":
    run()
