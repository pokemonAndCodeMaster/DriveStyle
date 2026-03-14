import pandas as pd
from typing import List
from src.domain.interfaces import BaseDataLoader
from src.domain.models import CarFollowingSegment, Vehicle, VehicleState

class CSVDataLoader(BaseDataLoader):
    def load_data(self, source: str) -> List[CarFollowingSegment]:
        df = pd.read_csv(source)
        ego_states = []
        target_states = []
        
        for _, row in df.iterrows():
            t = row.get('timestamp', 0)
            
            # Map mock CSV headers safely
            e_pos = 0.0 # CSV does not have ego_pos, it's relative
            e_vel = row.get('ego_velocity', 0.0)
            e_acc = row.get('ego_acceleration', 0.0)
            
            t_pos = row.get('relative_distance', 0.0)
            t_vel = row.get('lead_velocity', 0.0)
            t_acc = row.get('lead_acceleration', 0.0)
            
            ego_states.append(VehicleState(t, e_pos, e_vel, e_acc))
            target_states.append(VehicleState(t, t_pos, t_vel, t_acc))
            
        ego_v = Vehicle(vehicle_id="ego", states=ego_states)
        target_v = Vehicle(vehicle_id="target", states=target_states)
        
        return [CarFollowingSegment(segment_id="sim_segment_from_csv", ego_vehicle=ego_v, target_vehicle=target_v)]
