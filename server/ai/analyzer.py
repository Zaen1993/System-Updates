import os
import json
import time
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AnalyzerAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.model = IsolationForest(contamination=self.config.get("contamination", 0.01), random_state=42)
        self.data_buffer = []
        self.max_buffer = self.config.get("max_buffer", 1000)
        self.analysis_history = []
        self.error_tracker = None

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def process_task(self, task_type: str, data: Any) -> Dict[str, Any]:
        if task_type == "analyze_anomaly":
            return self.analyze_anomaly(data)
        elif task_type == "add_data":
            return self.add_data(data)
        elif task_type == "clear_buffer":
            self.clear_buffer()
            return {"status": "cleared"}
        return {"error": f"Unknown task type: {task_type}"}

    def add_data(self, data_point: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.data_buffer.append(data_point)
            if len(self.data_buffer) > self.max_buffer:
                self.data_buffer.pop(0)
            return {"status": "added", "buffer_size": len(self.data_buffer)}
        except Exception as e:
            logger.error(f"Error adding data: {e}")
            return {"error": str(e)}

    def analyze_anomaly(self, data: Any = None) -> Dict[str, Any]:
        try:
            if data is None and not self.data_buffer:
                return {"error": "No data to analyze"}
            df = None
            if data is not None:
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
            else:
                df = pd.DataFrame(self.data_buffer)
            if df.empty or len(df) < 10:
                return {"error": "Insufficient data (need at least 10 samples)"}
            # Select numeric columns only
            numeric_df = df.select_dtypes(include=[np.number])
            if numeric_df.shape[1] < 1:
                return {"error": "No numeric features found"}
            self.model.fit(numeric_df)
            preds = self.model.predict(numeric_df)
            anomaly_indices = np.where(preds == -1)[0].tolist()
            anomalies = df.iloc[anomaly_indices].to_dict(orient='records')
            result = {
                "total_samples": len(df),
                "anomalies_found": len(anomalies),
                "anomaly_indices": anomaly_indices,
                "anomalies": anomalies,
                "timestamp": time.time()
            }
            self.analysis_history.append(result)
            if len(self.analysis_history) > 100:
                self.analysis_history.pop(0)
            logger.info(f"Analysis complete: {len(anomalies)} anomalies out of {len(df)}")
            return result
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            if self.error_tracker:
                self.error_tracker.log_error("system", "ANALYZER_ERROR", str(e), module="analyzer")
            return {"error": str(e)}

    def clear_buffer(self):
        self.data_buffer.clear()

    def get_statistics(self) -> Dict:
        return {
            "buffer_size": len(self.data_buffer),
            "analyses_performed": len(self.analysis_history),
            "last_analysis": self.analysis_history[-1] if self.analysis_history else None
        }