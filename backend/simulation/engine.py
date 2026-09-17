"""
Pure-Python simulation engine — no FastAPI/DB dependency, so it can be
unit-tested directly. Moves each active delivery ("leg") along a list of
lat/lng waypoints (the resolved graph route) at a configurable speed,
tracking distance traveled, progress percentage, and completion.

The WebSocket router (routers/simulation.py) wraps this engine, ticking
it on a timer and broadcasting `get_state()` to connected clients, and is
responsible for translating completed legs into DB updates.
"""
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    R = 6371.0
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat = math.radians(b[0] - a[0])
    dlng = math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(h)))


@dataclass
class DriverLeg:
    leg_id: str          # unique id for this simulated trip, e.g. f"order-{order_id}"
    driver_id: int
    order_id: int
    driver_name: str
    waypoints: List[Tuple[float, float]]   # [(lat, lng), ...] from pickup to delivery
    speed_kmph: float = 25.0
    traveled_km: float = 0.0
    status: str = "running"    # running | completed

    cumulative_km: List[float] = field(default_factory=list, init=False)
    total_km: float = field(default=0.0, init=False)

    def __post_init__(self):
        cum = [0.0]
        for i in range(len(self.waypoints) - 1):
            cum.append(cum[-1] + _haversine_km(self.waypoints[i], self.waypoints[i + 1]))
        self.cumulative_km = cum
        self.total_km = cum[-1] if cum else 0.0

    def current_position(self) -> Tuple[float, float]:
        if self.total_km <= 0 or len(self.waypoints) == 1:
            return self.waypoints[0] if self.waypoints else (0.0, 0.0)

        traveled = min(self.traveled_km, self.total_km)
        # find the segment [i, i+1] containing `traveled`
        for i in range(len(self.cumulative_km) - 1):
            seg_start, seg_end = self.cumulative_km[i], self.cumulative_km[i + 1]
            if seg_start <= traveled <= seg_end or i == len(self.cumulative_km) - 2:
                seg_len = seg_end - seg_start
                t = 0.0 if seg_len == 0 else (traveled - seg_start) / seg_len
                t = max(0.0, min(1.0, t))
                lat1, lng1 = self.waypoints[i]
                lat2, lng2 = self.waypoints[i + 1]
                return (lat1 + (lat2 - lat1) * t, lng1 + (lng2 - lng1) * t)
        return self.waypoints[-1]

    def progress_pct(self) -> float:
        if self.total_km <= 0:
            return 100.0
        return round(min(100.0, (self.traveled_km / self.total_km) * 100.0), 1)

    def remaining_km(self) -> float:
        return max(0.0, self.total_km - self.traveled_km)

    def advance(self, dt_seconds: float, speed_multiplier: float = 1.0):
        if self.status == "completed":
            return
        km_this_tick = (self.speed_kmph * speed_multiplier) * (dt_seconds / 3600.0)
        self.traveled_km += km_this_tick
        if self.traveled_km >= self.total_km:
            self.traveled_km = self.total_km
            self.status = "completed"

    def to_state(self) -> dict:
        lat, lng = self.current_position()
        return {
            "leg_id": self.leg_id,
            "driver_id": self.driver_id,
            "order_id": self.order_id,
            "driver_name": self.driver_name,
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "progress_pct": self.progress_pct(),
            "traveled_km": round(self.traveled_km, 3),
            "remaining_km": round(self.remaining_km(), 3),
            "speed_kmph": self.speed_kmph,
            "status": self.status,
        }


class SimulationEngine:
    """Holds all active legs. `status` is one of: stopped | running | paused."""

    def __init__(self):
        self.legs: Dict[str, DriverLeg] = {}
        self.status: str = "stopped"
        self.speed_multiplier: float = 1.0

    def add_leg(self, leg: DriverLeg):
        self.legs[leg.leg_id] = leg

    def remove_leg(self, leg_id: str):
        self.legs.pop(leg_id, None)

    def clear(self):
        self.legs.clear()

    def start(self):
        self.status = "running"

    def pause(self):
        if self.status == "running":
            self.status = "paused"

    def resume(self):
        if self.status == "paused":
            self.status = "running"

    def stop(self):
        self.status = "stopped"

    def reset(self):
        self.legs.clear()
        self.status = "stopped"

    def tick(self, dt_seconds: float) -> List[dict]:
        """Advance all running legs; returns the list of legs that JUST completed this tick."""
        if self.status != "running":
            return []
        just_completed = []
        for leg in self.legs.values():
            was_running = leg.status == "running"
            leg.advance(dt_seconds, self.speed_multiplier)
            if was_running and leg.status == "completed":
                just_completed.append(leg.to_state())
        return just_completed

    def get_state(self) -> dict:
        return {
            "status": self.status,
            "speed_multiplier": self.speed_multiplier,
            "active_legs": [leg.to_state() for leg in self.legs.values() if leg.status == "running"],
            "completed_legs": [leg.to_state() for leg in self.legs.values() if leg.status == "completed"],
            "timestamp": time.time(),
        }
