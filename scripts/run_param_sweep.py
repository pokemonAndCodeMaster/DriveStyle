import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.loaders.factory import DataLoaderFactory
from src.identification.second_order_id import SecondOrderStyleIdentifier
from src.utils.visualization import MatplotlibVisualizer

def run_parameter_suite(file_path: str):
    """
    运行终极全维度参数对比套件。
    针对每个窗口大小，生成一张包含全量上下文、仿真对比、成本流与热力图的终极报告。
    """
    loader = DataLoaderFactory.get_loader(file_path)
    segments = loader.load_data(file_path)
    if not segments: return
    segment = segments[0]
    
    viz = MatplotlibVisualizer()
    thws = [1.0, 1.5, 2.0]
    wns = [0.4, 0.8, 1.4]
    window_sizes_sec = [1.0, 2.0, 3.0] # 测试 1s, 2s, 3s 窗口
    
    # --- Part 1: Global Physics Simulation ---
    sweep_results = []
    identifier = SecondOrderStyleIdentifier()
    print("Pre-computing Global Physics Simulations...")
    for wn in wns:
        for thw in thws:
            a_sim = identifier.simulate_segment(segment, thw=thw, wn=wn)
            mae = np.mean(np.abs(segment.ego_vehicle.get_accelerations() - a_sim))
            sweep_results.append({'thw': thw, 'wn': wn, 'a_sim': a_sim, 'mae': mae})
    
    # --- Part 2: Ultimate Suite Generation per Window Size ---
    for ws in window_sizes_sec:
        print(f"Generating Ultimate Comparison Suite for Window Size = {ws}s...")
        ws_frames = int(ws * 10) # 假设 10Hz
        all_wn_results = []
        
        for wn in wns:
            # 针对当前 wn 和 当前窗口大小运行动态辨识
            id_algo = SecondOrderStyleIdentifier(
                styles_config={t: {'wn': wn} for t in thws},
                window_size=ws_frames
            )
            res_df = id_algo.identify(segment)
            all_wn_results.append({'wn': wn, 'df': res_df})
            
        viz.plot_id_comparison_suite(segment, sweep_results, all_wn_results, window_size_sec=ws, 
                                    save_path=f"output/figures/ultimate_comp_Ws_{ws}s.png")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Full Parameter Comparison Suite")
    parser.add_argument("--file", default="debug.json", help="Test case file")
    args = parser.parse_args()
    
    run_parameter_suite(args.file)
