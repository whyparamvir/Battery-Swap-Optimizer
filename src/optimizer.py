"""
Battery Swap Station Optimizer
Greedy algorithm to minimize EV wait times at battery swap stations.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict
import heapq
from collections import defaultdict


@dataclass
class SwapStation:
    """A battery swap station with inventory and capacity."""
    id: int
    name: str
    location: Tuple[float, float]  # (lat, lon)
    battery_inventory: int         # Available fully-charged batteries
    swap_time_min: float           # Minutes per swap
    max_queue: int                 # Max vehicles in queue before rejecting

    def __repr__(self):
        return f"Station {self.id}: {self.name} (Inventory: {self.battery_inventory})"


@dataclass 
class Vehicle:
    """An EV requesting a battery swap."""
    id: int
    arrival_time: float            # Minutes from start
    location: Tuple[float, float]  # (lat, lon)
    battery_level_pct: float       # Current battery %
    urgency: str                   # 'low', 'medium', 'high', 'critical'

    def __repr__(self):
        return f"Vehicle {self.id} (Battery: {self.battery_level_pct}%, Urgency: {self.urgency})"


@dataclass
class Assignment:
    """Result of assigning a vehicle to a station."""
    vehicle_id: int
    station_id: int
    wait_time_min: float
    travel_time_min: float
    total_time_min: float
    assigned_at: float


class SwapOptimizer:
    """
    Greedy optimizer that assigns incoming vehicles to swap stations
    to minimize total weighted wait time (critical vehicles get priority).
    """

    URGENCY_WEIGHTS = {
        'critical': 10.0,
        'high': 3.0,
        'medium': 1.5,
        'low': 1.0
    }

    AVG_SPEED_KMH = 40  # Urban average speed

    def __init__(self, stations: List[SwapStation]):
        self.stations = {s.id: s for s in stations}
        self.queue_lengths = defaultdict(int)  # station_id -> current queue
        self.assignments: List[Assignment] = []
        self.station_history: Dict[int, List[Tuple[float, int]]] = defaultdict(list)

    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance in km between two coordinates."""
        import math
        R = 6371  # Earth radius in km

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _travel_time(self, vehicle: Vehicle, station: SwapStation) -> float:
        """Estimate travel time in minutes."""
        dist_km = self._haversine_distance(
            vehicle.location[0], vehicle.location[1],
            station.location[0], station.location[1]
        )
        return (dist_km / self.AVG_SPEED_KMH) * 60

    def _station_cost(self, vehicle: Vehicle, station: SwapStation) -> float:
        """
        Calculate cost of assigning vehicle to station.
        Lower cost = better assignment.
        """
        # Check capacity
        if self.queue_lengths[station.id] >= station.max_queue:
            return float('inf')

        # Check inventory
        if station.battery_inventory <= 0:
            return float('inf')

        travel_time = self._travel_time(vehicle, station)
        queue_wait = self.queue_lengths[station.id] * station.swap_time_min
        swap_time = station.swap_time_min

        total_wait = travel_time + queue_wait + swap_time

        # Weight by urgency - critical vehicles penalize long waits heavily
        weight = self.URGENCY_WEIGHTS.get(vehicle.urgency, 1.0)

        # Add small penalty for inventory depletion to balance load
        inventory_penalty = (10 / max(station.battery_inventory, 1)) * 0.1

        return (total_wait * weight) + inventory_penalty

    def optimize(self, vehicles: List[Vehicle]) -> List[Assignment]:
        """
        Run greedy optimization on a batch of vehicles.
        Processes vehicles in order of urgency then arrival time.
        """
        # Sort by urgency weight (descending) then arrival time
        sorted_vehicles = sorted(
            vehicles,
            key=lambda v: (-self.URGENCY_WEIGHTS.get(v.urgency, 1), v.arrival_time)
        )

        for vehicle in sorted_vehicles:
            best_station_id = None
            best_cost = float('inf')

            # Find best station
            for station in self.stations.values():
                cost = self._station_cost(vehicle, station)
                if cost < best_cost:
                    best_cost = cost
                    best_station_id = station.id

            if best_station_id is None:
                print(f"⚠️  Vehicle {vehicle.id} could not be assigned (all stations full)")
                continue

            station = self.stations[best_station_id]
            travel_time = self._travel_time(vehicle, station)
            queue_wait = self.queue_lengths[station.id] * station.swap_time_min
            swap_time = station.swap_time_min
            total_time = travel_time + queue_wait + swap_time

            # Record assignment
            assignment = Assignment(
                vehicle_id=vehicle.id,
                station_id=station.id,
                wait_time_min=queue_wait,
                travel_time_min=travel_time,
                total_time_min=total_time,
                assigned_at=vehicle.arrival_time
            )
            self.assignments.append(assignment)

            # Update station state
            self.queue_lengths[station.id] += 1
            station.battery_inventory -= 1
            self.station_history[station.id].append((vehicle.arrival_time, self.queue_lengths[station.id]))

        return self.assignments

    def get_stats(self) -> Dict:
        """Generate optimization statistics."""
        if not self.assignments:
            return {}

        total_wait = sum(a.wait_time_min for a in self.assignments)
        total_travel = sum(a.travel_time_min for a in self.assignments)
        total_times = [a.total_time_min for a in self.assignments]

        return {
            'total_vehicles': len(self.assignments),
            'avg_wait_time_min': total_wait / len(self.assignments),
            'avg_travel_time_min': total_travel / len(self.assignments),
            'avg_total_time_min': sum(total_times) / len(total_times),
            'max_total_time_min': max(total_times),
            'min_total_time_min': min(total_times),
            'station_utilization': {
                sid: len(hist) for sid, hist in self.station_history.items()
            }
        }
