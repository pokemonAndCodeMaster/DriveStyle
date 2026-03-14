import argparse
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.application.services.identification_service import IdentificationService
from src.identification.car_following_id import StyleIdentifier
from src.utils.visualization import MatplotlibVisualizer
from src.domain.interfaces import BaseIdentifier
import pandas as pd
import numpy as np

class IdentifierAdapter(BaseIdentifier):
    """Adapts CarFollowingSegment to the expected DataFrame format of StyleIdentifier."""
    def __init__(self, identifier: StyleIdentifier):
        self.identifier = identifier

    def identify(self, segment):
        df = segment.to_dataframe()
        # Rename columns to match what StyleIdentifier expects
        df = df.rename(columns={
            'lead_velocity': 'v_lv',
            'ego_velocity': 'v_ev',
            'relative_distance': 'dist',
            'ego_acceleration': 'a_ev'
        })
        
        # Use NaN for gt_style/scenario if missing to avoid misleading the user
        if 'gt_style' not in df.columns:
            df['gt_style'] = np.nan
        if 'scenario' not in df.columns:
            df['scenario'] = 'unknown'
            
        return self.identifier.identify(df)

def main():
    parser = argparse.ArgumentParser(description="Run identification and visualization on a single test case.")
    parser.add_argument("--file", required=True, help="Path to debug.json or test.csv")
    parser.add_argument("--out_dir", default="output/figures/", help="Output directory for plots")
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    core_identifier = StyleIdentifier()
    identifier = IdentifierAdapter(core_identifier)
    visualizer = MatplotlibVisualizer()
    service = IdentificationService(identifier, visualizer)
    
    print(f"Running single case analysis on: {args.file}")
    
    # First, visualize the segment itself
    from src.infrastructure.loaders.factory import DataLoaderFactory
    loader = DataLoaderFactory.get_loader(args.file)
    segments = loader.load_data(args.file)
    print(f"Extracted {len(segments)} valid car-following segments.")
    for seg in segments:
        visualizer.plot_segment(seg, os.path.join(args.out_dir, f"{os.path.basename(args.file)}_{seg.segment_id}_dynamics.png"))

    # Then run the identification which will output results
    results = service.run_on_file(args.file, output_path=os.path.join(args.out_dir, f"{os.path.basename(args.file)}_id_result"))
    
    for seg_id, res_df in results:
        print(f"\n--- Result for Segment {seg_id} ---")
        if not res_df.empty:
            print(res_df[['start_time', 'identified_style', 'valid_ratio']])
        else:
            print("No valid identification results (clip too short or missing fields).")

if __name__ == "__main__":
    main()
