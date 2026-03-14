import argparse
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.application.services.identification_service import IdentificationService
from src.identification.car_following_id import StyleIdentifier
from src.utils.visualization import MatplotlibVisualizer
from scripts.run_single_case import IdentifierAdapter

def main():
    parser = argparse.ArgumentParser(description="Batch verification of multiple test cases.")
    parser.add_argument("--dir", default="tests/data", help="Directory containing test cases (.json or .csv)")
    parser.add_argument("--out", default="output/data/batch_report.csv", help="Path for aggregated batch report")
    parser.add_argument("--plot_limit", type=int, default=3, help="Max number of segment plots to generate (0 for none)")
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    
    core_identifier = StyleIdentifier()
    identifier = IdentifierAdapter(core_identifier)
    visualizer = MatplotlibVisualizer()
    service = IdentificationService(identifier, visualizer)
    
    all_reports = []
    plot_count = 0
    
    print(f"Starting batch validation in directory: {args.dir}")
    if not os.path.exists(args.dir):
        print(f"Directory {args.dir} not found. Please generate test cases first.")
        return

    for file in os.listdir(args.dir):
        if file.endswith(('.json', '.csv')):
            filepath = os.path.join(args.dir, file)
            print(f"Processing: {filepath}")
            try:
                # Decide whether to plot based on limit
                should_plot = plot_count < args.plot_limit
                results = service.run_on_file(filepath, plot_segments=should_plot)
                
                for seg_id, res_df in results:
                    if not res_df.empty:
                        res_df['source_file'] = file
                        all_reports.append(res_df)
                        if should_plot: plot_count += 1
            except Exception as e:
                print(f"Error processing {file}: {e}")
    
    if all_reports:
        batch_report = pd.concat(all_reports, ignore_index=True)
        # Reorder columns for readability
        cols = ['segment_id', 'target_id', 'start_time', 'end_time', 'identified_style']
        if 'gt_style' in batch_report.columns: cols.append('gt_style')
        cols += ['valid_ratio', 'total_duration', 'avg_v_ego', 'avg_dist', 'source_file']
        # Add cost columns
        cols += [c for c in batch_report.columns if c.startswith('cost_')]
        
        batch_report = batch_report[cols]
        batch_report.to_csv(args.out, index=False)
        print(f"\nBatch processing complete. Aggregated report saved to {args.out}")
        
        # Generate summary visualizations
        print("Generating summary batch visualizations...")
        visualizer.plot_batch_results(batch_report, save_dir="output/figures/")
    else:
        print("\nNo valid results generated.")

if __name__ == "__main__":
    main()
