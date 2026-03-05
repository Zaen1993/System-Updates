import logging
import hashlib
import time
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class OSINTIndexer:
    def __init__(self):
        self._index: Dict[str, Dict[str, Any]] = {}
        logger.info("OSINTIndexer initialized")

    def index_data(self, source: str, content: str, metadata: Optional[Dict] = None) -> str:
        doc_id = hashlib.sha256(f"{source}{content}{time.time()}".encode()).hexdigest()[:16]
        self._index[doc_id] = {
            "source": source,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        logger.debug(f"Indexed {doc_id} from {source}")
        return doc_id

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        for doc_id, doc in self._index.items():
            if q in doc["content"].lower():
                results.append({
                    "id": doc_id,
                    "source": doc["source"],
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "timestamp": doc["timestamp"],
                    "score": 1.0
                })
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results[:limit]

    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        return [{"id": doc_id, **doc} for doc_id, doc in self._index.items() if doc["source"] == source]

    def remove(self, doc_id: str) -> bool:
        if doc_id in self._index:
            del self._index[doc_id]
            return True
        return False

    def stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self._index),
            "sources": list(set(d["source"] for d in self._index.values()))
        }

    def export(self) -> Dict[str, Any]:
        return {"index": self._index}

    def load(self, data: Dict[str, Any]) -> None:
        self._index = data.get("index", {})