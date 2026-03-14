import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from typing import Any, List, Union, Dict
from sklearn.metrics import confusion_matrix
from src.domain.interfaces import BaseVisualizer
from src.domain.models import CarFollowingSegment

class MatplotlibVisualizer(BaseVisualizer):
    """
    旗舰级自动驾驶算法研判可视化器 (V14.0 数据实验室版)
    """
    def __init__(self, style: str = "whitegrid", context: str = "talk"):
        sns.set_theme(style=style, context=context)
        self.output_dir = "output/figures/"
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_results(self, data: Any, output_path: str = None):
        pass

    def plot_ultimate_comparison(self, segment: CarFollowingSegment, 
                                 results_list: List[Dict[str, Any]], 
                                 window_size_sec: float,
                                 title_suffix: str = "",
                                 save_path: str = None):
        """
        生成全维度对比画布。包含物理一致性推演射线。
        """
        df = segment.to_dataframe()
        times = df['timestamp'].values
        v_ego, v_lead = df['ego_velocity'].values * 3.6, df['lead_velocity'].values * 3.6
        a_actual, a_lead = df['ego_acceleration'].values, df['lead_acceleration'].values
        thw_obs = np.where(v_ego > 0.1, df['relative_distance'] / (v_ego / 3.6), np.nan)
        style_colors = {1.0: '#e74c3c', 1.5: '#f39c12', 2.0: '#27ae60'}
        thw_targets = [1.0, 1.5, 2.0]

        total_rows = 1 + len(results_list)
        fig = plt.figure(figsize=(30, 7 * total_rows))
        gs = fig.add_gridspec(total_rows, 3, hspace=0.4, wspace=0.2)

        # Row 0: Global Context
        ax_v = fig.add_subplot(gs[0, 0:2])
        l1, = ax_v.plot(times, v_lead, color='#95a5a6', linewidth=2, linestyle='--', label="Lead Vel (km/h)")
        l2, = ax_v.plot(times, v_ego, color='#2980b9', linewidth=3, label="Ego Vel (km/h)")
        ax_a = ax_v.twinx()
        l3, = ax_a.plot(times, a_lead, color='#34495e', alpha=0.3, linestyle=':', label="Lead Accel")
        l4, = ax_a.plot(times, a_actual, color='#8e44ad', alpha=0.6, linewidth=2, label="Actual Ego Accel")
        ax_v.set_title(f"Global Diagnostic | Ws: {window_size_sec}s {title_suffix}", fontsize=22, fontweight='bold')
        ax_v.legend([l1, l2, l3, l4], [l.get_label() for l in [l1, l2, l3, l4]], loc='upper right', ncol=2)
        ax_v.grid(True, alpha=0.3)

        ax_t = fig.add_subplot(gs[0, 2])
        ax_t.plot(times, thw_obs, color='#2c3e50', linewidth=2.5, label="Observed THW")
        for t_val in thw_targets: ax_t.axhline(y=t_val, color=style_colors[t_val], linestyle='--', alpha=0.5)
        ax_t.set_ylim(max(0.5, np.nanmin(thw_obs)-0.2), min(4.0, np.nanmax(thw_obs)+0.2))
        ax_t.grid(True, alpha=0.3)

        # Rows 1-N: Per-Parameter Pair
        for i, res in enumerate(results_list):
            wn, zeta, res_df = res['wn'], res['zeta'], res['df']
            row_idx = i + 1
            # 1. Accel Planning
            ax_acc = fig.add_subplot(gs[row_idx, 0])
            ax_acc.plot(times, a_actual, color='#bdc3c7', linewidth=4, alpha=0.3)
            ax_acc.plot(times, a_lead, color='#34495e', linewidth=1, linestyle=':', alpha=0.5)
            if not res_df.empty:
                for idx in range(0, len(res_df), 10):
                    item = res_df.iloc[idx]
                    for t_target, ray in item['acc_rays'].items():
                        ax_acc.plot(np.arange(len(ray))*0.1 + item['start_time'], ray, color=style_colors[t_target], alpha=0.5, linewidth=1.5)
            ax_acc.set_title(f"Accel Planning (wn={wn}, z={zeta})", fontweight='bold')
            # 2. THW Predictions
            ax_rays = fig.add_subplot(gs[row_idx, 1])
            ax_rays.plot(times, thw_obs, color='#2c3e50', linewidth=1.5, alpha=0.4, zorder=2)
            all_ray_vals = [thw_obs]
            if not res_df.empty:
                for idx in range(0, len(res_df), 10):
                    item = res_df.iloc[idx]
                    for t_target, ray in item['rays'].items():
                        ax_rays.plot(np.arange(len(ray))*0.1 + item['start_time'], ray, color=style_colors[t_target], alpha=0.6, linewidth=2.0, zorder=5)
                        all_ray_vals.append(ray)
            flat = np.concatenate([np.atleast_1d(rv) for rv in all_ray_vals])
            ax_rays.set_ylim(max(0.5, np.nanmin(flat)-0.1), min(3.5, np.nanmax(flat)+0.1))
            ax_rays.set_title(f"THW Long-Horizon Convergence (10s)", fontweight='bold')
            # 3. Cost Streams
            ax_c = fig.add_subplot(gs[row_idx, 2])
            for t_val in thw_targets:
                col = f"cost_{t_val}"
                if col in res_df.columns: ax_c.plot(res_df['start_time'], res_df[col], color=style_colors[t_val], linewidth=2, label=f"{t_val}s")
            ax_c.set_title(f"MAE Residual Costs")
            ax_c.legend(loc='upper right', fontsize='small')

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def plot_sensitivity_heatmaps(self, sweep_results: List[Dict[str, Any]], save_path: str = None):
        """
        生成切片式热力图，对比不同 zeta 下的 wn-THW 敏感度。
        """
        if save_path is None: save_path = os.path.join(self.output_dir, "param_sensitivity_heatmaps.png")
        df = pd.DataFrame(sweep_results)
        zetas = sorted(df['zeta'].unique())
        fig, axes = plt.subplots(1, len(zetas), figsize=(8 * len(zetas), 7))
        if len(zetas) == 1: axes = [axes]
        for i, z in enumerate(zetas):
            slice_df = df[df['zeta'] == z].pivot(index='wn', columns='thw', values='mae')
            sns.heatmap(slice_df, annot=True, fmt=".3f", cmap="YlOrRd_r", ax=axes[i])
            axes[i].set_title(f"Cost Sensitivity (zeta={z})")
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
