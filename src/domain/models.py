from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
import pandas as pd

@dataclass
class VehicleState:
    timestamp: float
    position: float
    velocity: float
    acceleration: float

@dataclass
class Vehicle:
    vehicle_id: str
    states: List[VehicleState] = field(default_factory=list)

    def get_velocities(self) -> np.ndarray:
        return np.array([s.velocity for s in self.states])

    def get_positions(self) -> np.ndarray:
        return np.array([s.position for s in self.states])

    def get_accelerations(self) -> np.ndarray:
        return np.array([s.acceleration for s in self.states])
    
    def get_timestamps(self) -> np.ndarray:
        return np.array([s.timestamp for s in self.states])

@dataclass
class CarFollowingSegment:
    segment_id: str
    ego_vehicle: Vehicle
    target_vehicle: Vehicle
    target_id: str = "unknown"
    start_timestamp: float = 0.0
    end_timestamp: float = 0.0
    
    @property
    def duration(self) -> float:
        return self.end_timestamp - self.start_timestamp

    @property
    def relative_distance(self) -> np.ndarray:
        return self.target_vehicle.get_positions() - self.ego_vehicle.get_positions()
    
    @property
    def relative_velocity(self) -> np.ndarray:
        return self.target_vehicle.get_velocities() - self.ego_vehicle.get_velocities()

    def to_dataframe(self) -> pd.DataFrame:
        """Converts the segment data into a pandas DataFrame for vectorized analysis."""
        return pd.DataFrame({
            'timestamp': self.ego_vehicle.get_timestamps(),
            'ego_velocity': self.ego_vehicle.get_velocities(),
            'ego_acceleration': self.ego_vehicle.get_accelerations(),
            'lead_velocity': self.target_vehicle.get_velocities(),
            'lead_acceleration': self.target_vehicle.get_accelerations(),
            'relative_distance': self.relative_distance,
            'relative_velocity': self.relative_velocity
        })
