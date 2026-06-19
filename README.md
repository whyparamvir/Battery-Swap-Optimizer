# 🔋 Battery Swap Station Optimizer

A Python-based greedy optimization algorithm that assigns EVs to battery swap stations to minimize total weighted wait time.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## What It Does

Given a network of battery swap stations (with inventory, capacity, and location) and a stream of incoming EVs (with battery level, urgency, and location), the optimizer assigns each vehicle to the best station using a **greedy cost-minimization algorithm** that considers:

- **Travel time** (Haversine distance / average speed)
- **Queue wait time** (current queue length × swap time)
- **Urgency weighting** (critical vehicles get 10× priority)
- **Inventory balancing** (prefers stations with more batteries)

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/battery-swap-optimizer.git
cd battery-swap-optimizer
pip install -r requirements.txt

# Run the demo
python src/demo.py

# Generate visualizations
python src/visualize.py

# Run tests
python -m pytest src/test_optimizer.py -v
```

## Project Structure

```
battery-swap-optimizer/
├── src/
│   ├── optimizer.py      # Core algorithm (greedy cost minimization)
│   ├── demo.py           # CLI demo with sample NYC network
│   ├── visualize.py      # Matplotlib charts + interactive Leaflet map
│   └── test_optimizer.py # Unit tests (pytest)
├── requirements.txt
└── README.md
```

## Algorithm Details

### Cost Function

```
Cost = (travel_time + queue_wait + swap_time) × urgency_weight + inventory_penalty
```

Where:
- `urgency_weight`: critical=10, high=3, medium=1.5, low=1
- `inventory_penalty`: 1 / inventory (discourages depleting single stations)

### Complexity
- **Time**: O(V × S) where V = vehicles, S = stations
- **Space**: O(V + S)

## Sample Output

```
Station Utilization
  Station 1 (Downtown Hub): ████████░░ 8/10
  Station 2 (Airport Station): ██████████ 10/10
  Station 3 (Brooklyn Depot): ████░░░░░░ 4/6

Average Total Time: 12.4 min
Max Total Time: 28.1 min
```

## Visualizations

| Chart | Description |
|-------|-------------|
| `optimization_results.png` | 4-panel analysis: utilization, time distribution, scatter plot, time breakdown |
| `interactive_map.html` | Leaflet map with color-coded station load (green/orange/red) |

## Future Improvements

- [ ] Linear programming (PuLP) for global optimum
- [ ] Dynamic rebalancing (move batteries between stations)
- [ ] Real-time API integration (Google Maps for traffic-aware routing)
- [ ] Monte Carlo simulation for demand forecasting

## Why This Matters

Battery swap networks (NIO, Ample, Gogoro) are critical infrastructure for EV adoption in dense urban areas. Efficient assignment algorithms directly impact:
- **Customer satisfaction** (lower wait times)
- **Station profitability** (higher throughput)
- **Grid stability** (predictable demand patterns)

## License

MIT
