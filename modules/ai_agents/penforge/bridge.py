import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

    def query(self, prompt: str) -> str:
        try:
            import openai
            openai.api_key = self.api_key
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return "analysis_failed"

class ToolExecutor:
    def __init__(self):
        self.tools = {
            "scan": self._scan,
            "exploit": self._exploit,
            "enum": self._enumerate
        }

    def _scan(self, target: str) -> Dict[str, Any]:
        logger.info(f"Scanning target: {target}")
        return {"status": "scan_completed", "target": target, "result": "dummy_scan_result"}

    def _exploit(self, target: str) -> Dict[str, Any]:
        logger.info(f"Exploiting target: {target}")
        return {"status": "exploit_attempted", "target": target, "result": "dummy_exploit_result"}

    def _enumerate(self, target: str) -> Dict[str, Any]:
        logger.info(f"Enumerating target: {target}")
        return {"status": "enum_completed", "target": target, "result": "dummy_enum_result"}

    def run(self, action: str, target: str) -> Dict[str, Any]:
        func = self.tools.get(action, self._scan)
        return func(target)

class PentestGPTBridge:
    def __init__(self, api_key: str = None):
        self.llm = LLMClient(api_key)
        self.executor = ToolExecutor()
        logger.info("PentestGPTBridge initialized")

    def analyze_and_act(self, target_info: str, tool_output: str) -> Dict[str, Any]:
        logger.info("Analyzing tool output with LLM")
        prompt = f"Target: {target_info}\nTool Output: {tool_output}\nWhat is the next step? Answer with one word: scan, exploit, enum, or stop."
        decision = self.llm.query(prompt).strip().lower()
        if decision not in ["scan", "exploit", "enum"]:
            decision = "stop"
        if decision == "stop":
            return {"action": "stop", "result": "no further action"}
        result = self.executor.run(decision, target_info)
        return {"action": decision, "result": result}

if __name__ == "__main__":
    bridge = PentestGPTBridge()
    print("PentestGPTBridge ready")