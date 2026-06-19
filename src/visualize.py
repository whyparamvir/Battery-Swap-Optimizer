"""
Visualization tools for the Battery Swap Optimizer.
Generates static charts and an interactive HTML map.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import json
from typing import Dict, List
from pathlib import Path


def plot_optimization_results(optimizer, stats, output_dir="."):
    """Generate comprehensive result charts."""
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

    # 1. Station Utilization Bar Chart
    ax1 = fig.add_subplot(gs[0, 0])
    station_ids = list(stats["station_utilization"].keys())
    counts = list(stats["station_utilization"].values())
    colors = ["#2ecc71" if c < 5 else "#f39c12" if c < 8 else "#e74c3c" for c in counts]

    bars = ax1.bar(station_ids, counts, color=colors, edgecolor="black", linewidth=1.2)
    ax1.set_xlabel("Station ID", fontsize=12)
    ax1.set_ylabel("Vehicles Served", fontsize=12)
    ax1.set_title("Station Utilization", fontsize=14, fontweight="bold")
    ax1.set_xticks(station_ids)

    # Legend
    green = mpatches.Patch(color="#2ecc71", label="Low Load")
    yellow = mpatches.Patch(color="#f39c12", label="Medium Load")
    red = mpatches.Patch(color="#e74c3c", label="High Load")
    ax1.legend(handles=[green, yellow, red], loc="upper right")

    # 2. Time Distribution Histogram
    ax2 = fig.add_subplot(gs[0, 1])
    total_times = [a.total_time_min for a in optimizer.assignments]
    ax2.hist(total_times, bins=15, color="#3498db", edgecolor="black", alpha=0.8)
    ax2.axvline(stats["avg_total_time_min"], color="red", linestyle="--", linewidth=2, 
               label=f"Mean: {stats['avg_total_time_min']:.1f} min")
    ax2.set_xlabel("Total Time (minutes)", fontsize=12)
    ax2.set_ylabel("Number of Vehicles", fontsize=12)
    ax2.set_title("Total Service Time Distribution", fontsize=14, fontweight="bold")
    ax2.legend()

    # 3. Wait Time vs Travel Time Scatter
    ax3 = fig.add_subplot(gs[1, 0])
    wait_times = [a.wait_time_min for a in optimizer.assignments]
    travel_times = [a.travel_time_min for a in optimizer.assignments]
    ax3.scatter(travel_times, wait_times, c="#9b59b6", alpha=0.6, s=60, edgecolors="black")
    ax3.set_xlabel("Travel Time (minutes)", fontsize=12)
    ax3.set_ylabel("Queue Wait Time (minutes)", fontsize=12)
    ax3.set_title("Travel vs Queue Wait Time", fontsize=14, fontweight="bold")
    ax3.grid(True, alpha=0.3)

    # 4. Time Components Pie
    ax4 = fig.add_subplot(gs[1, 1])
    avg_travel = stats["avg_travel_time_min"]
    avg_wait = stats["avg_wait_time_min"]
    avg_swap = sum(a.total_time_min - a.travel_time_min - a.wait_time_min 
                   for a in optimizer.assignments) / len(optimizer.assignments)

    components = [avg_travel, avg_wait, avg_swap]
    labels = ["Travel", "Queue Wait", "Swap Service"]
    colors_pie = ["#3498db", "#e74c3c", "#2ecc71"]

    ax4.pie(components, labels=labels, colors=colors_pie, autopct="%1.1f%%", 
           startangle=90, textprops={"fontsize": 11})
    ax4.set_title("Average Time Breakdown", fontsize=14, fontweight="bold")

    plt.suptitle("Battery Swap Station Optimization Results", fontsize=16, fontweight="bold", y=0.98)

    output_path = Path(output_dir) / "optimization_results.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    print(f"Chart saved: {output_path}")
    return str(output_path)


def generate_interactive_map(optimizer, output_dir="."):
    """Generate an interactive HTML map with stations and assignments."""

    stations_data = []
    for sid, station in optimizer.stations.items():
        utilization = len(optimizer.station_history.get(sid, []))
        stations_data.append({
            "id": sid,
            "name": station.name,
            "lat": station.location[0],
            "lon": station.location[1],
            "inventory": station.battery_inventory,
            "utilization": utilization,
            "max_queue": station.max_queue
        })

    stations_json = json.dumps(stations_data)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Battery Swap Network</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }}
        #map {{ height: 100vh; width: 100%; }}
        .info-panel {{
            position: absolute; top: 10px; right: 10px;
            background: white; padding: 15px; border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 1000;
            min-width: 200px;
        }}
        .info-panel h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .station-item {{ margin: 5px 0; padding: 5px; border-radius: 4px; font-size: 13px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3>Swap Stations</h3>
        <div id="station-list"></div>
        <hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">
        <p style="font-size: 12px; color: #666; margin: 0;">
            <strong>Green:</strong> Low load<br>
            <strong>Orange:</strong> Medium load<br>
            <strong>Red:</strong> High load
        </p>
    </div>

    <script>
        const map = L.map('map').setView([40.73, -73.95], 11);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: 'OpenStreetMap'
        }}).addTo(map);

        const stations = {stations_json};

        stations.forEach(s => {{
            const loadRatio = s.utilization / s.max_queue;
            let color = loadRatio < 0.5 ? '#2ecc71' : loadRatio < 0.8 ? '#f39c12' : '#e74c3c';
            let radius = 8 + (s.utilization * 0.5);

            const marker = L.circleMarker([s.lat, s.lon], {{
                color: color, fillColor: color, fillOpacity: 0.7, radius: radius
            }}).addTo(map);

            marker.bindPopup(
                '<strong>' + s.name + '</strong><br>' +
                'ID: ' + s.id + '<br>' +
                'Served: ' + s.utilization + ' vehicles<br>' +
                'Remaining inventory: ' + s.inventory + '<br>' +
                'Capacity: ' + s.max_queue
            );
        }});

        const list = document.getElementById('station-list');
        stations.forEach(s => {{
            const div = document.createElement('div');
            div.className = 'station-item';
            div.style.background = s.utilization / s.max_queue < 0.5 ? '#e8f8f5' : 
                                   s.utilization / s.max_queue < 0.8 ? '#fef5e7' : '#fdedec';
            div.innerHTML = '<strong>' + s.name + '</strong>: ' + s.utilization + ' served';
            list.appendChild(div);
        }});
    </script>
</body>
</html>"""

    output_path = Path(output_dir) / "interactive_map.html"
    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"Interactive map saved: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    from demo import main
    optimizer, stats = main()

    plot_optimization_results(optimizer, stats, output_dir=".")
    generate_interactive_map(optimizer, output_dir=".")

    print("\nAll visualizations generated!")
