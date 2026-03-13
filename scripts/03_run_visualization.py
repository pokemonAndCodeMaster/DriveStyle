import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.visualization import plot_confusion_matrix, plot_scenario_performance, plot_dynamic_residuals

def main():
    sim_path = "output/data/simulation_dataset.csv"
    iden_path = "output/data/identification_results.csv"
    
    if not os.path.exists(sim_path) or not os.path.exists(iden_path):
        print("Error: Required data files not found. Run simulation and identification first.")
        return

    print("Loading data...")
    sim_df = pd.read_csv(sim_path)
    iden_df = pd.read_csv(iden_path)
    
    print("Generating statistical plots...")
    plot_confusion_matrix(iden_df)
    plot_scenario_performance(iden_df)
    
    print("Generating scenario-specific dynamic residual plots...")
    # 选一个典型的波动工况 (Sine)
    sine_ids = sim_df[sim_df['scenario'] == 'sine']['scenario_id'].unique()
    if len(sine_ids) > 0:
        plot_dynamic_residuals(sim_df, iden_df, scenario_id=sine_ids[0])
        
    # 选一个具有挑战性的减速工况 (Emergency)
    emergency_ids = sim_df[sim_df['scenario'] == 'emergency']['scenario_id'].unique()
    if len(emergency_ids) > 0:
        plot_dynamic_residuals(sim_df, iden_df, scenario_id=emergency_ids[0])
        
    print("Visualization pipeline completed successfully. Check output/figures/ directory.")

if __name__ == "__main__":
    main()
