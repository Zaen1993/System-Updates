import os
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import pickle
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("C2_DB_PATH", "/data/c2_data.db")
MODEL_DIR = os.environ.get("MODEL_DIR", "/models")

def load_data(device_id: str, hours: int = 72):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT latitude, longitude, timestamp FROM location_logs
        WHERE device_id = ? AND timestamp > datetime('now', ?)
        ORDER BY timestamp ASC
    """
    cutoff = f"-{hours} hours"
    df = pd.read_sql_query(query, conn, params=(device_id, cutoff))
    conn.close()
    if df.empty:
        return None
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['time_num'] = (df['timestamp'] - datetime(1970,1,1)).dt.total_seconds()
    return df

def train_and_predict(df, model_type='linear'):
    if df is None or len(df) < 5:
        return None
    X = df[['time_num']].values
    y_lat = df['latitude'].values
    y_lon = df['longitude'].values
    if model_type == 'linear':
        model_lat = LinearRegression()
        model_lon = LinearRegression()
    else:
        model_lat = RandomForestRegressor(n_estimators=10, max_depth=5)
        model_lon = RandomForestRegressor(n_estimators=10, max_depth=5)
    model_lat.fit(X, y_lat)
    model_lon.fit(X, y_lon)
    last_time = df['time_num'].iloc[-1]
    future_time = np.array([[last_time + 3600]])
    pred_lat = model_lat.predict(future_time)[0]
    pred_lon = model_lon.predict(future_time)[0]
    return {"lat": float(pred_lat), "lon": float(pred_lon), "time": datetime.fromtimestamp(future_time[0][0]).isoformat()}

def predict_future_location(device_id: str):
    try:
        df = load_data(device_id)
        if df is None:
            logger.warning(f"No data for device {device_id}")
            return {"error": "Insufficient data"}
        result = train_and_predict(df, model_type='linear')
        return result if result else {"error": "Prediction failed"}
    except Exception as e:
        logger.exception(f"Prediction error: {e}")
        return {"error": str(e)}

def save_model(device_id, model_lat, model_lon):
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(f"{MODEL_DIR}/{device_id}_lat.pkl", 'wb') as f:
        pickle.dump(model_lat, f)
    with open(f"{MODEL_DIR}/{device_id}_lon.pkl", 'wb') as f:
        pickle.dump(model_lon, f)

def load_model(device_id):
    lat_path = f"{MODEL_DIR}/{device_id}_lat.pkl"
    lon_path = f"{MODEL_DIR}/{device_id}_lon.pkl"
    if os.path.exists(lat_path) and os.path.exists(lon_path):
        with open(lat_path, 'rb') as f:
            model_lat = pickle.load(f)
        with open(lon_path, 'rb') as f:
            model_lon = pickle.load(f)
        return model_lat, model_lon
    return None, None

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        dev = sys.argv[1]
        res = predict_future_location(dev)
        print(res)
    else:
        print("Usage: python predictive_analysis.py <device_id>")