"""
Battery Swap Station Optimizer - Demo Runner
Run this to see the optimizer in action with sample data.
"""

from optimizer import SwapStation, Vehicle, SwapOptimizer
import random


def create_sample_network():
    """Create a realistic urban swap station network."""
    stations = [
        SwapStation(id=1, name="Downtown Hub", location=(40.7128, -74.0060), 
                   battery_inventory=15, swap_time_min=3, max_queue=8),
        SwapStation(id=2, name="Airport Station", location=(40.7769, -73.8740),
                   battery_inventory=20, swap_time_min=2.5, max_queue=10),
        SwapStation(id=3, name="Brooklyn Depot", location=(40.6782, -73.9442),
                   battery_inventory=12, swap_time_min=4, max_queue=6),
        SwapStation(id=4, name="Queens Center", location=(40.7282, -73.7949),
                   battery_inventory=18, swap_time_min=3, max_queue=9),
        SwapStation(id=5, name="Jersey City Port", location=(40.7178, -74.0431),
                   battery_inventory=10, swap_time_min=3.5, max_queue=5),
    ]
    return stations


def generate_vehicle_demand(num_vehicles=50, seed=42):
    """Generate random vehicle demand around NYC area."""
    random.seed(seed)

    urgencies = ['low', 'medium', 'high', 'critical']
    weights = [0.4, 0.35, 0.2, 0.05]  # 5% critical

    vehicles = []
    for i in range(num_vehicles):
        # Random location within ~20km of NYC center
        lat = 40.7128 + random.uniform(-0.3, 0.3)
        lon = -74.0060 + random.uniform(-0.4, 0.4)

        # Arrival times spread over 2 hours (120 minutes)
        arrival = random.expovariate(1/15)  # Poisson process, avg 15 min intervals
        arrival = min(arrival, 120)  # Cap at 120 min

        urgency = random.choices(urgencies, weights=weights)[0]
        battery = random.uniform(5, 40)  # 5-40% battery

        vehicles.append(Vehicle(
            id=i+1,
            arrival_time=arrival,
            location=(lat, lon),
            battery_level_pct=battery,
            urgency=urgency
        ))

    return vehicles


def print_results(optimizer, stats):
    """Pretty print optimization results."""
    print("\n" + "="*60)
    print("🔋 BATTERY SWAP STATION OPTIMIZER RESULTS")
    print("="*60)

    print(f"\n📊 SUMMARY")
    print(f"   Total Vehicles Assigned: {stats['total_vehicles']}")
    print(f"   Average Wait Time: {stats['avg_wait_time_min']:.2f} min")
    print(f"   Average Travel Time: {stats['avg_travel_time_min']:.2f} min")
    print(f"   Average Total Time: {stats['avg_total_time_min']:.2f} min")
    print(f"   Max Total Time: {stats['max_total_time_min']:.2f} min")
    print(f"   Min Total Time: {stats['min_total_time_min']:.2f} min")

    print(f"\n🏢 STATION UTILIZATION")
    for sid, count in stats['station_utilization'].items():
        station = optimizer.stations[sid]
        bar = "█" * count + "░" * (station.max_queue - count)
        print(f"   Station {sid} ({station.name}): {bar} {count}/{station.max_queue}")

    print(f"\n🚗 SAMPLE ASSIGNMENTS (first 10)")
    print(f"   {'Vehicle':<10} {'Station':<10} {'Wait':<8} {'Travel':<8} {'Total':<8}")
    print(f"   {'-'*44}")
    for a in optimizer.assignments[:10]:
        print(f"   {a.vehicle_id:<10} {a.station_id:<10} {a.wait_time_min:<8.1f} {a.travel_time_min:<8.1f} {a.total_time_min:<8.1f}")


def main():
    print("🔋 Battery Swap Station Optimizer")
    print("="*40)

    # Setup
    stations = create_sample_network()
    vehicles = generate_vehicle_demand(num_vehicles=50)

    print(f"\n📍 Network: {len(stations)} stations")
    for s in stations:
        print(f"   • {s}")

    print(f"\n🚗 Demand: {len(vehicles)} vehicles")

    # Run optimization
    optimizer = SwapOptimizer(stations)
    assignments = optimizer.optimize(vehicles)
    stats = optimizer.get_stats()

    # Results
    print_results(optimizer, stats)

    return optimizer, stats


if __name__ == "__main__":
    main()
