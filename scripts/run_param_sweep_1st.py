import os
import sys
import numpy as np
import pandas as pd
from typing import List, Dict, Any

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config_manager import ConfigManager
from src.infrastructure.loaders.factory import DataLoaderFactory
from src.identification.car_following_id import StyleIdentifier
from src.utils.visualization import MatplotlibVisualizer
from src.domain.models import CarFollowingSegment

class SweepRunner1stOrder:
    def __init__(self, file_path: str):
        self.cfg = ConfigManager()
        # Ensure file_path is absolute if possible
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
        self.file_path = file_path
        self.loader = DataLoaderFactory.get_loader(file_path)
        self.segments = self.loader.load_data(file_path)
        self.viz = MatplotlibVisualizer()
        
        # 定义扫参范围
        self.lambdas = [0.2, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        self.thws_sweep = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        self.window_sizes = [1.0, 2.0, 3.0] # seconds

    def run(self):
        if not self.segments:
            print(f"[ERROR] No segments found in {self.file_path}")
            return
        
        # 为演示目的，只对第一个片段进行深入分析
        segment = self.segments[0]
        print(f"Analyzing Segment: {segment.segment_id} ({len(segment.ego_vehicle.states)} frames)")
        
        # 1. 敏感度扫频 (Heatmap)
        sweep_data = self._run_sensitivity_sweep(segment)
        # 为了适配 viz.plot_sensitivity_heatmaps，将 lambda 映射为 wn, zeta 设为 1.0
        viz_sweep_data = []
        for d in sweep_data:
            viz_sweep_data.append({
                'wn': d['lambda'],
                'thw': d['thw'],
                'zeta': 1.0,
                'mae': d['mae']
            })
        
        heatmap_path = os.path.join("output/figures/", "param_sensitivity_heatmaps_1st.png")
        self.viz.plot_sensitivity_heatmaps(viz_sweep_data, save_path=heatmap_path)
        print(f"[SUCCESS] Heatmap saved to {heatmap_path}")
        
        # 2. 终极对比图 (Ultimate Comparison)
        selected_lambdas = [0.5, 1.0, 2.0]
        for ws_sec in self.window_sizes:
            dt = self.cfg.get('physics.dt', 0.1)
            ws_frames = int(ws_sec / dt)
            combo_res = []
            for lb in selected_lambdas:
                # 注意：StyleIdentifier 的 target_thws 必须是可视化器支持的 [1.0, 1.5, 2.0]
                algo = StyleIdentifier(target_thws=[1.0, 1.5, 2.0], window_size=ws_frames, lambda_default=lb)
                res_df = algo.identify(segment)
                # 适配可视化器：wn -> lambda, zeta -> 1.0
                combo_res.append({'wn': lb, 'zeta': 1.0, 'df': res_df})
            
            save_path = os.path.join("output/figures/", f"ultimate_comp_1st_Ws_{ws_sec}s.png")
            self.viz.plot_ultimate_comparison(segment, combo_res, window_size_sec=ws_sec, title_suffix="| 1st Order", save_path=save_path)
            print(f"[SUCCESS] Ultimate comparison saved to {save_path}")

    def _run_sensitivity_sweep(self, segment: CarFollowingSegment) -> List[Dict[str, Any]]:
        print("Running 1st Order Sensitivity Sweep...")
        data = []
        algo = StyleIdentifier()
        actual_acc = segment.to_dataframe()['ego_acceleration'].values
        
        for lb in self.lambdas:
            for t_ref in self.thws_sweep:
                # 调用重构后的接口
                res_sim = algo.simulate_segment(segment, t_ref, lb)
                acc_ray = res_sim['acc']
                
                # 确保长度一致进行 MAE 计算
                min_len = min(len(actual_acc), len(acc_ray))
                mae = np.mean(np.abs(actual_acc[:min_len] - acc_ray[:min_len]))
                
                data.append({
                    'lambda': lb,
                    'thw': t_ref,
                    'mae': mae
                })
        return data

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="debug.json")
    args = parser.parse_args()
    
    # 转换为绝对路径
    file_path = args.file
    if not os.path.isabs(file_path):
        project_root = "/home/yyh/projects/DriveStyle"
        file_path = os.path.join(project_root, args.file)

    runner = SweepRunner1stOrder(file_path)
    runner.run()
