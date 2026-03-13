import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.identification.car_following_id import StyleIdentifier

def main():
    data_path = "output/data/simulation_dataset.csv"
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}. Run simulation first.")
        return

    df_all = pd.read_csv(data_path)
    identifier = StyleIdentifier()
    
    all_results = []
    scenario_ids = df_all['scenario_id'].unique()
    
    print(f"Identifying styles for {len(scenario_ids)} scenarios...")
    for sid in scenario_ids:
        scenario_df = df_all[df_all['scenario_id'] == sid]
        res = identifier.identify(scenario_df)
        res['scenario_id'] = sid
        all_results.append(res)
        
    final_res = pd.concat(all_results)
    
    out_path = "output/data/identification_results.csv"
    final_res.to_csv(out_path, index=False)
    print(f"Identification completed. Results saved to {out_path}")

    final_res['match'] = np.isclose(final_res['identified_style'], final_res['gt_style'], atol=0.1)
    accuracy = final_res['match'].mean()
    print(f"Overall Identification Accuracy: {accuracy:.2%}")

if __name__ == "__main__":
    main()
