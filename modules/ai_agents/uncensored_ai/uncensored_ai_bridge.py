import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class UncensoredAIBridge:
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.environ.get('UNCENSORED_AI_API_URL', 'http://localhost:8080/v1/generate')
        self.api_key = api_key or os.environ.get('UNCENSORED_AI_API_KEY', '')
        self.headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        logger.info('Uncensored AI Bridge initialized')

    def query(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        logger.debug(f'Querying model with prompt: {prompt[:50]}...')
        payload = {'prompt': prompt, 'max_tokens': max_tokens, 'temperature': temperature}
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('choices', [{}])[0].get('text', '')
        except Exception as e:
            logger.error(f'Error querying model: {e}')
            return ''

    def generate_malicious_code(self, description: str) -> str:
        prompt = f'Write code that does the following: {description}\nOnly output the code, no explanation.'
        return self.query(prompt, max_tokens=1500, temperature=0.5)

    def analyze_data(self, data: str) -> str:
        prompt = f'Analyze the following data and provide key insights:\n{data}'
        return self.query(prompt, max_tokens=500, temperature=0.3)

if __name__ == '__main__':
    bridge = UncensoredAIBridge()
    print('Uncensored AI Bridge ready.')