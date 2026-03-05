import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional
from bleak import BleakScanner, BleakClient

logger = logging.getLogger(__name__)

class BLEScanner:
    def __init__(self, scan_interval: int = 5):
        self.scan_interval = scan_interval
        self.devices: Dict[str, dict] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _start_async_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._scan_forever())

    def start_scanning(self):
        if self._running:
            logger.warning("scanning already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self._thread.start()
        logger.info("ble scanning started")

    def stop_scanning(self):
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("ble scanning stopped")

    async def _scan_forever(self):
        while self._running:
            try:
                devices = await BleakScanner.discover(timeout=5, return_adv=True)
                for addr, (adv_data, adv) in devices.items():
                    self.devices[addr] = {
                        "name": adv_data.local_name or "Unknown",
                        "rssi": adv.rssi,
                        "manufacturer_data": adv.manufacturer_data,
                        "service_uuids": adv.service_uuids,
                        "last_seen": time.time()
                    }
                logger.debug(f"found {len(devices)} ble devices")
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"scan error: {e}")
                await asyncio.sleep(5)

    def scan_for_devices(self) -> Dict[str, dict]:
        async def _scan_once():
            devices = await BleakScanner.discover(timeout=5, return_adv=True)
            result = {}
            for addr, (adv_data, adv) in devices.items():
                result[addr] = {
                    "name": adv_data.local_name or "Unknown",
                    "rssi": adv.rssi,
                    "manufacturer_data": adv.manufacturer_data,
                    "service_uuids": adv.service_uuids,
                    "last_seen": time.time()
                }
            return result

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices = loop.run_until_complete(_scan_once())
            self.devices.update(devices)
            return devices
        finally:
            loop.close()

    def get_cached_devices(self) -> Dict[str, dict]:
        return self.devices

    async def _connect_and_read(self, address: str, char_uuid: str) -> Optional[bytes]:
        try:
            async with BleakClient(address) as client:
                logger.info(f"connected to {address}")
                if await client.is_connected():
                    data = await client.read_gatt_char(char_uuid)
                    return data
                return None
        except Exception as e:
            logger.error(f"connection/read error for {address}: {e}")
            return None

    def connect_to_device(self, address: str, char_uuid: str = "") -> bool:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data = loop.run_until_complete(self._connect_and_read(address, char_uuid))
            if char_uuid:
                return data is not None
            return True
        finally:
            loop.close()

    def get_device_info(self, address: str) -> Optional[dict]:
        return self.devices.get(address)

if __name__ == "__main__":
    scanner = BLEScanner()
    found = scanner.scan_for_devices()
    for addr, info in found.items():
        print(f"{addr}: {info['name']} (RSSI: {info['rssi']})")