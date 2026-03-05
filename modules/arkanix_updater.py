import os
import logging
import requests
import hashlib
import json
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArkanixUpdater:
    def __init__(self, update_server_url: str, component_name: str = "system"):
        self.update_server_url = update_server_url.rstrip('/')
        self.component_name = component_name
        self.current_version = self._get_local_version()
        logger.info(f"Updater initialized for {self.component_name}")

    def _get_local_version(self) -> str:
        """Read local version from a version file."""
        version_file = f"{self.component_name}.version"
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        return "0.0.0"

    def _set_local_version(self, version: str) -> None:
        """Write current version to a file."""
        version_file = f"{self.component_name}.version"
        with open(version_file, 'w') as f:
            f.write(version)

    def check_updates(self) -> Optional[Dict[str, Any]]:
        """Query the update server for new version metadata."""
        try:
            url = f"{self.update_server_url}/check/{self.component_name}/{self.current_version}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("update_available"):
                    logger.info(f"Update available: {data['version']}")
                    return data
                else:
                    logger.info("No updates available.")
            else:
                logger.warning(f"Update check failed with status {resp.status_code}")
        except Exception as e:
            logger.error(f"Update check error: {e}")
        return None

    def fetch_package(self, download_url: str, expected_hash: str) -> Optional[bytes]:
        """Download the update package and verify its integrity."""
        try:
            logger.info(f"Downloading from {download_url}")
            resp = requests.get(download_url, timeout=30)
            if resp.status_code != 200:
                logger.error(f"Download failed: {resp.status_code}")
                return None
            data = resp.content
            computed = hashlib.sha256(data).hexdigest()
            if computed != expected_hash:
                logger.error("Hash mismatch. Package corrupted.")
                return None
            logger.info("Package verified successfully.")
            return data
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

    def apply_package(self, package_data: bytes) -> bool:
        """Apply the update (e.g., replace files, restart services)."""
        # Placeholder: actual deployment logic goes here.
        # For a server component, this might involve extracting an archive,
        # stopping services, overwriting files, and restarting.
        logger.info("Applying update package...")
        try:
            # Simulate successful update
            # In real code, you would handle file extraction and verification
            self._set_local_version("1.2.0")  # example new version
            logger.info("Update applied successfully.")
            return True
        except Exception as e:
            logger.error(f"Apply failed: {e}")
            return False

    def run_update_cycle(self) -> bool:
        """Perform the full update check, fetch, and apply cycle."""
        update_info = self.check_updates()
        if not update_info:
            return False
        package = self.fetch_package(update_info['download_url'], update_info['hash'])
        if not package:
            return False
        return self.apply_package(package)

if __name__ == "__main__":
    # Example usage (not executed in production)
    updater = ArkanixUpdater("https://updates.example.com", "core")
    updater.run_update_cycle()