import json
import logging
from typing import List, Optional, Dict, Any
from src.domain.interfaces import BaseDataLoader
from src.domain.models import CarFollowingSegment, Vehicle, VehicleState

logger = logging.getLogger(__name__)

class JSONDataLoader(BaseDataLoader):
    def load_data(self, source: str) -> List[CarFollowingSegment]:
        try:
            with open(source, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f'Failed to load JSON file {source}: {e}')
            return []

        if not isinstance(data, list):
            logger.error(f'JSON data in {source} is not a list.')
            return []

        segments: List[CarFollowingSegment] = []
        current_frames: List[Dict[str, Any]] = []
        current_front_id = None

        for frame in data:
            follow_data_raw = frame.get('17010900', {})
            follow_data = follow_data_raw[0] if isinstance(follow_data_raw, list) and len(follow_data_raw)>0 else follow_data_raw
            if not isinstance(follow_data, dict): follow_data = {}

            is_follow_list = follow_data.get('17010900_description_is_follow', [])
            front_id_list = follow_data.get('17010900_description_front_id', [])
            is_follow = is_follow_list[0] if is_follow_list else False
            front_id = front_id_list[0] if front_id_list else None

            if is_follow and front_id is not None:
                if current_front_id is None:
                    current_front_id = front_id
                    current_frames = [frame]
                elif front_id == current_front_id:
                    current_frames.append(frame)
                else:
                    if len(current_frames) >= 50:
                        segments.append(self._create_segment(current_frames, current_front_id))
                    current_front_id = front_id
                    current_frames = [frame]
            else:
                if len(current_frames) >= 50:
                    segments.append(self._create_segment(current_frames, current_front_id))
                current_frames = []
                current_front_id = None

        if len(current_frames) >= 50:
            segments.append(self._create_segment(current_frames, current_front_id))

        logger.info(f'Loaded {len(segments)} segments from {source}')
        return segments

    def _create_segment(self, frames: List[Dict[str, Any]], front_id: Any) -> CarFollowingSegment:
        ego_vehicle = Vehicle(vehicle_id='ego')
        target_vehicle = Vehicle(vehicle_id=str(front_id))
        
        for frame in frames:
            try:
                timestamp = float(frame.get('timestamp', 0))
                
                ego_info_raw = frame.get('23010101', {})
                ego_info = ego_info_raw[0] if isinstance(ego_info_raw, list) and len(ego_info_raw)>0 else ego_info_raw
                if not isinstance(ego_info, dict): ego_info = {}

                v_ego_list = ego_info.get('23010101_description_velocity', [0])
                a_ego_list = ego_info.get('23010101_description_acc_longi', [0])
                v_ego = float(v_ego_list[0]) if v_ego_list else 0.0
                a_ego = float(a_ego_list[0]) if a_ego_list else 0.0
                
                follow_data_raw = frame.get('17010900', {})
                follow_info = follow_data_raw[0] if isinstance(follow_data_raw, list) and len(follow_data_raw)>0 else follow_data_raw
                if not isinstance(follow_info, dict): follow_info = {}

                dist_list = follow_info.get('17010900_description_following_distance', [0])
                v_lead_list = follow_info.get('17010900_description_front_speed', [0])
                a_lead_list = follow_info.get('17010900_description_front_acc', [0])
                dist = float(dist_list[0]) if dist_list else 0.0
                v_lead = float(v_lead_list[0]) if v_lead_list else 0.0
                a_lead = float(a_lead_list[0]) if a_lead_list else 0.0
                
                ego_state = VehicleState(timestamp=timestamp, position=0.0, velocity=v_ego, acceleration=a_ego)
                target_state = VehicleState(timestamp=timestamp, position=dist, velocity=v_lead, acceleration=a_lead)
                ego_vehicle.states.append(ego_state)
                target_vehicle.states.append(target_state)
            except (ValueError, IndexError, TypeError):
                continue
                
        segment_id = f'segment_{front_id}_{frames[0].get("timestamp", "0")}'
        return CarFollowingSegment(
            segment_id=segment_id, 
            ego_vehicle=ego_vehicle, 
            target_vehicle=target_vehicle,
            target_id=str(front_id),
            start_timestamp=float(frames[0].get("timestamp", 0.0)),
            end_timestamp=float(frames[-1].get("timestamp", 0.0))
        )
