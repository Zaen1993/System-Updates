import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse

logger = logging.getLogger(__name__)

class MatrixBridge:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.homeserver = self.config.get("homeserver", os.environ.get("MATRIX_HOMESERVER", "https://matrix.org"))
        self.user_id = self.config.get("user_id", os.environ.get("MATRIX_USER"))
        self.password = self.config.get("password", os.environ.get("MATRIX_PASSWORD"))
        self.device_id = self.config.get("device_id", "matrix_bridge")
        self.room_id = self.config.get("room_id")
        self.client: Optional[AsyncClient] = None
        self.access_token = None
        self.sync_token = None
        self.running = False
        self.loop = None
        self._callbacks = []
        self._crypto = None

    def set_crypto(self, crypto_manager):
        """Inject crypto agility manager for encrypted messages."""
        self._crypto = crypto_manager

    async def connect(self) -> bool:
        """Login to Matrix homeserver and start sync."""
        if not self.user_id or not self.password:
            logger.error("Matrix credentials missing")
            return False

        self.client = AsyncClient(self.homeserver, self.user_id, device_id=self.device_id)
        try:
            resp = await self.client.login(self.password)
            if isinstance(resp, LoginResponse):
                self.access_token = resp.access_token
                logger.info(f"Logged into Matrix as {self.user_id}")
                return True
            else:
                logger.error(f"Matrix login failed: {resp}")
                return False
        except Exception as e:
            logger.exception(f"Matrix connection error: {e}")
            return False

    async def sync_forever(self):
        """Continuously sync and handle messages."""
        if not self.client:
            if not await self.connect():
                return

        self.running = True
        while self.running:
            try:
                sync_response = await self.client.sync(timeout=30000, since=self.sync_token)
                self.sync_token = sync_response.next_batch

                # Process joined rooms
                for room_id, room in sync_response.rooms.join.items():
                    for event in room.timeline.events:
                        if isinstance(event, RoomMessageText):
                            await self._handle_message(room_id, event)
            except Exception as e:
                logger.exception(f"Matrix sync error: {e}")
                await asyncio.sleep(10)

    async def _handle_message(self, room_id: str, event: RoomMessageText):
        """Process incoming message, decrypt if needed, and trigger callbacks."""
        body = event.body
        sender = event.sender
        logger.info(f"Matrix message from {sender} in {room_id}: {body}")

        # If message looks like base64, try to decrypt
        if self._crypto and len(body) > 44 and body.strip().endswith('='):
            try:
                import base64
                encrypted = base64.b64decode(body)
                decrypted = self._crypto.decrypt_data(encrypted)
                body = decrypted.decode('utf-8')
                logger.debug("Message decrypted")
            except Exception as e:
                logger.warning(f"Could not decrypt message: {e}")

        for cb in self._callbacks:
            try:
                await cb(room_id, sender, body)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def send_command(self, room_id: str, command: str, encrypt: bool = False) -> bool:
        """Send a command (optionally encrypted) to a room."""
        if not self.client:
            if not await self.connect():
                return False

        body = command
        if encrypt and self._crypto:
            try:
                encrypted = self._crypto.encrypt_data(body.encode())
                import base64
                body = base64.b64encode(encrypted).decode()
            except Exception as e:
                logger.error(f"Encryption failed: {e}")
                return False

        try:
            content = {"msgtype": "m.text", "body": body}
            await self.client.room_send(room_id, "m.room.message", content)
            logger.info(f"Sent command to {room_id}")
            return True
        except Exception as e:
            logger.exception(f"Failed to send command: {e}")
            return False

    def register_callback(self, callback):
        """Register async function to handle incoming commands."""
        self._callbacks.append(callback)

    async def stop(self):
        """Stop sync and close client."""
        self.running = False
        if self.client:
            await self.client.close()

    def run_in_background(self, loop=None):
        """Run sync_forever in a background asyncio task."""
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        loop.create_task(self.sync_forever())