import os
import sys
import numpy as np
import pandas as pd
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config_manager import ConfigManager
from src.infrastructure.loaders.factory import DataLoaderFactory
from src.identification.second_order_id import SecondOrderStyleIdentifier
from src.utils.visualization import MatplotlibVisualizer

class ExperimentRunner:
    """
    实验运行器：解耦实验逻辑，支持自动化扫参与报告生成。
    """
    def __init__(self, file_path: str):
        self.cfg = ConfigManager()
        self.file_path = file_path
        self.loader = DataLoaderFactory.get_loader(file_path)
        self.segments = self.loader.load_data(file_path)
        self.viz = MatplotlibVisualizer()
        
        self.thws = self.cfg.get('identification.targets.thw')
        self.wns = self.cfg.get('identification.targets.wn')
        self.zetas = self.cfg.get('identification.targets.zeta')

    def run_full_suite(self):
        if not self.segments: return
        segment = self.segments[0]
        
        # 1. 敏感度热力图分析
        sweep_data = self._run_sensitivity_sweep(segment)
        self.viz.plot_sensitivity_heatmaps(sweep_data)
        
        # 2. 全维度画布生成
        window_sizes = self.cfg.get('experiment.window_sizes_test')
        for ws in window_sizes:
            self._run_diagnostic_plots(segment, ws)
            
        # 3. 量化报表导出
        self._export_master_report(sweep_data)

    def _run_sensitivity_sweep(self, segment) -> List[Dict[str, Any]]:
        print("Step 1: Running Sensitivity Sweep...")
        data = []
        algo = SecondOrderStyleIdentifier()
        for z in self.zetas:
            for w in self.wns:
                for t in self.thws:
                    sim = algo.simulate_segment(segment, thw=t, wn=w, zeta=z)
                    mae = np.mean(np.abs(segment.ego_vehicle.get_accelerations() - sim['acc']))
                    
                    # 收敛特征提取
                    ss_error = abs(sim['thw'][-1] - t)
                    settle_t = 10.0
                    for idx, val in enumerate(sim['thw']):
                        if abs(val - t) < 0.05:
                            settle_t = idx * 0.1
                            break
                    
                    data.append({
                        'thw': t, 'wn': w, 'zeta': z, 'mae': mae,
                        'jerk_var': np.var(np.diff(sim['acc'])/0.1),
                        'settle_t': settle_t, 'ss_error': ss_error,
                        'sim_acc_mean': np.mean(sim['acc']), 'sim_thw_mean': np.mean(sim['thw'])
                    })
        return data

    def _run_diagnostic_plots(self, segment, ws_sec: float):
        print(f"Step 2: Drawing Diagnostic Canvas (Ws={ws_sec}s)...")
        ws_frames = int(ws_sec * 10)
        for wn in self.wns:
            combo_res = []
            for zeta in self.zetas:
                algo = SecondOrderStyleIdentifier(
                    config={t: {'wn': wn, 'zeta': zeta} for t in self.thws},
                    window_size=ws_frames
                )
                res_df = algo.identify(segment)
                combo_res.append({'wn': wn, 'zeta': zeta, 'df': res_df})
            
            save_path = os.path.join(self.cfg.get('experiment.output_dir'), f"ultimate_Ws_{ws_sec}s_wn_{wn}.png")
            self.viz.plot_ultimate_comparison(segment, combo_res, window_size_sec=ws_sec, title_suffix=f"| wn={wn}", save_path=save_path)

    def _export_master_report(self, sweep_data):
        print("Step 3: Exporting Quantitative Master Report...")
        rows = []
        for r in sweep_data:
            rows.append({
                'Param_THW': r['thw'], 'Param_wn': r['wn'], 'Param_zeta': r['zeta'],
                'MAE': f"{r['mae']:.4f}", 'JerkVar': f"{r['jerk_var']:.4f}",
                'SettleTime': f"{r['settle_t']:.2f}s", 'SSE': f"{r['ss_error']:.4f}",
                'Mean_Accel': f"{r['sim_acc_mean']:.4f}", 'Mean_THW': f"{r['sim_thw_mean']:.4f}"
            })
        report_path = os.path.join(self.cfg.get('experiment.report_dir'), "ultimate_master_report.csv")
        pd.DataFrame(rows).to_csv(report_path, index=False)
        print(f"[SUCCESS] Report saved to {report_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="debug.json")
    args = parser.parse_args()
    
    runner = ExperimentRunner(args.file)
    runner.run_full_suite()
