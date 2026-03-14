from typing import List
from src.domain.interfaces import BaseDataLoader, BaseIdentifier, BaseVisualizer
from src.infrastructure.loaders.factory import DataLoaderFactory

class IdentificationService:
    def __init__(self, identifier: BaseIdentifier, visualizer: BaseVisualizer = None):
        self.identifier = identifier
        self.visualizer = visualizer

    def run_on_file(self, data_file: str, output_path: str = None, plot_segments: bool = True):
        loader = DataLoaderFactory.get_loader(data_file)
        segments = loader.load_data(data_file)
        
        results = []
        for segment in segments:
            id_df = self.identifier.identify(segment)
            
            # Enrich with segment-level metadata
            if not id_df.empty:
                id_df['segment_id'] = segment.segment_id
                id_df['target_id'] = segment.target_id
                id_df['total_duration'] = segment.duration
                id_df['avg_v_ego'] = segment.ego_vehicle.get_velocities().mean()
                id_df['avg_dist'] = segment.relative_distance.mean()
            
            results.append((segment.segment_id, id_df))
            
            if self.visualizer and plot_segments:
                save_file = f"{output_path}_{segment.segment_id}.png" if output_path else None
                # Pass both segment and results for integrated visualization
                self.visualizer.plot_segment(segment, id_results=id_df, save_path=save_file)
        
        return results
