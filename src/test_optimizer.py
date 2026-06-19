"""
Unit tests for the Battery Swap Optimizer.
Run with: python -m pytest test_optimizer.py -v
"""

import pytest
from optimizer import SwapStation, Vehicle, SwapOptimizer


class TestSwapOptimizer:

    def test_basic_assignment(self):
        """Test that a single vehicle gets assigned to the nearest station."""
        stations = [
            SwapStation(id=1, name="Near", location=(40.0, -74.0), 
                       battery_inventory=5, swap_time_min=3, max_queue=10),
            SwapStation(id=2, name="Far", location=(41.0, -75.0),
                       battery_inventory=5, swap_time_min=3, max_queue=10),
        ]

        vehicles = [
            Vehicle(id=1, arrival_time=0, location=(40.01, -74.01), 
                   battery_level_pct=20, urgency="medium")
        ]

        optimizer = SwapOptimizer(stations)
        assignments = optimizer.optimize(vehicles)

        assert len(assignments) == 1
        assert assignments[0].station_id == 1  # Should pick nearest

    def test_critical_priority(self):
        """Test that critical vehicles get priority in queue."""
        stations = [
            SwapStation(id=1, name="Solo", location=(40.0, -74.0),
                       battery_inventory=1, swap_time_min=5, max_queue=1),
        ]

        vehicles = [
            Vehicle(id=1, arrival_time=0, location=(40.0, -74.0),
                   battery_level_pct=30, urgency="low"),
            Vehicle(id=2, arrival_time=0, location=(40.0, -74.0),
                   battery_level_pct=5, urgency="critical"),
        ]

        optimizer = SwapOptimizer(stations)
        assignments = optimizer.optimize(vehicles)

        # Critical vehicle should be assigned first
        assert len(assignments) == 1
        assert assignments[0].vehicle_id == 2

    def test_capacity_limit(self):
        """Test that stations reject vehicles when at max queue."""
        stations = [
            SwapStation(id=1, name="Tiny", location=(40.0, -74.0),
                       battery_inventory=10, swap_time_min=2, max_queue=2),
        ]

        vehicles = [
            Vehicle(id=i, arrival_time=0, location=(40.0, -74.0),
                   battery_level_pct=20, urgency="medium")
            for i in range(1, 5)
        ]

        optimizer = SwapOptimizer(stations)
        assignments = optimizer.optimize(vehicles)

        # Only 2 should be assigned (max_queue)
        assert len(assignments) == 2

    def test_inventory_depletion(self):
        """Test that stations run out of batteries."""
        stations = [
            SwapStation(id=1, name="Limited", location=(40.0, -74.0),
                       battery_inventory=2, swap_time_min=2, max_queue=10),
        ]

        vehicles = [
            Vehicle(id=i, arrival_time=0, location=(40.0, -74.0),
                   battery_level_pct=20, urgency="medium")
            for i in range(1, 5)
        ]

        optimizer = SwapOptimizer(stations)
        assignments = optimizer.optimize(vehicles)

        # Only 2 should be assigned (inventory limit)
        assert len(assignments) == 2

    def test_stats_calculation(self):
        """Test that statistics are calculated correctly."""
        stations = [
            SwapStation(id=1, name="Test", location=(40.0, -74.0),
                       battery_inventory=10, swap_time_min=3, max_queue=10),
        ]

        vehicles = [
            Vehicle(id=1, arrival_time=0, location=(40.0, -74.0),
                   battery_level_pct=20, urgency="medium"),
        ]

        optimizer = SwapOptimizer(stations)
        optimizer.optimize(vehicles)
        stats = optimizer.get_stats()

        assert stats["total_vehicles"] == 1
        assert stats["avg_wait_time_min"] == 0.0  # No queue
        assert "avg_travel_time_min" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
