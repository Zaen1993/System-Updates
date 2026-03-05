import re
import logging

logger = logging.getLogger(__name__)

class KeyloggerAnalyzer:
    def __init__(self):
        self.extracted_data = []
        self.patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'password_keywords': ['pass', 'password', 'pwd'],
        }

    def clean_keystrokes(self, raw: str) -> str:
        replacements = {
            '[SPACE]': ' ',
            '[ENTER]': '\n',
            '[TAB]': '\t',
            '[BACKSPACE]': '',
        }
        for token, repl in replacements.items():
            raw = raw.replace(token, repl)
        return raw

    def extract_sensitive(self, text: str) -> list:
        found = []
        emails = re.findall(self.patterns['email'], text)
        if emails:
            found.extend(emails)
        for line in text.splitlines():
            lower = line.lower()
            if any(key in lower for key in self.patterns['password_keywords']):
                found.append(line.strip())
        return found

    def analyze(self, raw_data: str) -> dict:
        cleaned = self.clean_keystrokes(raw_data)
        sensitive = self.extract_sensitive(cleaned)
        result = {
            'cleaned': cleaned,
            'sensitive': sensitive,
        }
        if sensitive:
            logger.info(f"Found {len(sensitive)} sensitive items")
            self.extracted_data.append(result)
        return result