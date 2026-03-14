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
    专业级自动驾驶算法研判可视化器 (V9.1 物理校准版)
    """
    def __init__(self, style: str = "whitegrid", context: str = "talk"):
        sns.set_theme(style=style, context=context)
        self.output_dir = "output/figures/"
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_results(self, data: Any, output_path: str = None):
        if isinstance(data, CarFollowingSegment):
            self.plot_segment(data, id_results=None, save_path=output_path)
        elif isinstance(data, pd.DataFrame):
            self.plot_batch_results(data, output_path)

    def plot_segment(self, segment: CarFollowingSegment, id_results: pd.DataFrame = None, save_path: str = None):
        # 简单单片段图逻辑 (略)
        pass

    def plot_id_comparison_suite(self, segment: CarFollowingSegment, 
                                 sweep_results: List[Dict[str, Any]],
                                 all_id_results: List[Dict[str, Any]], 
                                 window_size_sec: float,
                                 save_path: str = None):
        """
        终极研判看板：解决遮挡、对齐物理、稀疏化推演。
        """
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"ultimate_Ws_{window_size_sec}s.png")

        df = segment.to_dataframe()
        times, v_ego, v_lead = df['timestamp'].values, df['ego_velocity'].values * 3.6, df['lead_velocity'].values * 3.6
        a_actual, a_lead, dist = df['ego_acceleration'].values, df['lead_acceleration'].values, df['relative_distance'].values
        thw_obs = np.where(v_ego > 0.1, dist / (v_ego / 3.6), np.nan)
        thws = sorted(list(set([r['thw'] for r in sweep_results])))
        wns = sorted(list(set([r['wn'] for r in all_id_results])), reverse=True)
        style_colors = {1.0: '#e74c3c', 1.5: '#f39c12', 2.0: '#27ae60'}

        total_rows = 2 + len(wns)
        fig = plt.figure(figsize=(28, 6 * total_rows))
        gs = fig.add_gridspec(total_rows, 3, hspace=0.4, wspace=0.2)

        # --- Row 0: Global context ---
        ax_v = fig.add_subplot(gs[0, 0:2])
        l1, = ax_v.plot(times, v_lead, color='#95a5a6', linewidth=2, linestyle='--', label="Lead Velocity (km/h)")
        l2, = ax_v.plot(times, v_ego, color='#2980b9', linewidth=3, label="Ego Velocity (km/h)")
        ax_a = ax_v.twinx()
        l3, = ax_a.plot(times, a_lead, color='#2c3e50', alpha=0.4, linestyle=':', label="Lead Accel (m/s²)")
        l4, = ax_a.plot(times, a_actual, color='#8e44ad', alpha=0.7, linewidth=2.5, label="Actual Ego Accel (m/s²)")
        ax_v.legend([l1, l2, l3, l4], [l.get_label() for l in [l1, l2, l3, l4]], loc='upper right', framealpha=0.9, ncol=2)
        ax_v.set_title(f"Diagnostic Report | Window: {window_size_sec}s", fontsize=24, fontweight='bold', pad=20)
        ax_v.set_ylabel("Velocity (km/h)", fontweight='bold')
        ax_a.set_ylabel("Acceleration (m/s²)", color='#8e44ad', fontweight='bold')
        ax_v.grid(True, alpha=0.3)

        ax_t = fig.add_subplot(gs[0, 2])
        ax_t.plot(times, thw_obs, color='#2c3e50', linewidth=2.5, label="Observed THW")
        for t_val in thws: ax_t.axhline(y=t_val, color=style_colors.get(t_val, '#7f8c8d'), linestyle='--', alpha=0.5)
        ax_t.set_title("Global THW Trend", fontsize=16, fontweight='bold')
        y_min, y_max = np.nanmin(thw_obs), np.nanmax(thw_obs)
        ax_t.set_ylim(max(0.5, y_min - 0.2), min(4.0, y_max + 0.2))
        ax_t.grid(True, alpha=0.3)

        # --- Middle Rows: Rolling Predictions ---
        for i, wn in enumerate(wns):
            res_df = next(r['df'] for r in all_id_results if r['wn'] == wn)
            
            # 1. Accel Planning (Rolling Rays)
            ax_acc = fig.add_subplot(gs[i+1, 0])
            ax_acc.plot(times, a_actual, color='#bdc3c7', linewidth=4, alpha=0.3, label="Actual $a_{ego}$")
            ax_acc.plot(times, a_lead, color='#2c3e50', linewidth=1, linestyle=':', alpha=0.5, label="Lead $a_{lead}$")
            if not res_df.empty:
                for idx in range(0, len(res_df), 10): # 稀疏化：每隔 1.0s 一个射线
                    row = res_df.iloc[idx]
                    for t_target, ray_a in row['acc_rays'].items():
                        c = style_colors.get(t_target, '#7f8c8d')
                        ray_t = np.arange(len(ray_a)) * 0.1 + row['start_time']
                        ax_acc.plot(ray_t, ray_a, color=c, alpha=0.5, linewidth=1.5)
            ax_acc.set_title(f"Accel Planning ($\omega_n$={wn})", fontsize=14, fontweight='bold')
            ax_acc.set_ylabel("Accel (m/s²)")
            ax_acc.grid(True, alpha=0.2)

            # 2. THW Convergence (Rolling Rays)
            ax_rays = fig.add_subplot(gs[i+1, 1])
            ax_rays.plot(times, thw_obs, color='#2c3e50', linewidth=1.5, alpha=0.4, label="Actual", zorder=2)
            all_ray_vals = [thw_obs]
            if not res_df.empty:
                for idx in range(0, len(res_df), 10): # 稀疏化：每隔 1.0s
                    row = res_df.iloc[idx]
                    for t_target, ray_t_data in row['rays'].items():
                        c = style_colors.get(t_target, '#7f8c8d')
                        ray_t = np.arange(len(ray_t_data)) * 0.1 + row['start_time']
                        ax_rays.plot(ray_t, ray_t_data, color=c, alpha=0.6, linewidth=2.0, zorder=5)
                        all_ray_vals.append(ray_t_data)
            
            flat_rays = np.concatenate([np.atleast_1d(rv) for rv in all_ray_vals])
            ax_rays.set_ylim(max(0.5, np.nanmin(flat_rays)-0.1), min(3.5, np.nanmax(flat_rays)+0.1))
            ax_rays.set_title(f"THW Intent Convergence ($\omega_n$={wn})", fontsize=14, fontweight='bold')
            ax_rays.grid(True, alpha=0.2)

            # 3. Cost Streams
            ax_c = fig.add_subplot(gs[i+1, 2])
            for t_val in thws:
                col = f"cost_{t_val}"
                if col in res_df.columns:
                    ax_c.plot(res_df['start_time'], res_df[col], color=style_colors[t_val], linewidth=2, label=f"Cost {t_val}s")
            ax_c.set_title(f"Residual Cost Integrals ($\omega_n$={wn})", fontsize=14, fontweight='bold')
            ax_c.legend(loc='upper right', fontsize='small')
            ax_c.grid(True, alpha=0.2)

        # --- Bottom ---
        ax_dec = fig.add_subplot(gs[-1, 0:2])
        for wn in wns:
            res_df = next(r['df'] for r in all_id_results if r['wn'] == wn)
            ax_dec.step(res_df['start_time'], res_df['identified_style'], where='post', linewidth=2.5, marker='o', markersize=5, label=f"Decision ($\omega_n$={wn})")
        ax_dec.set_ylim(0.5, 2.5)
        ax_dec.set_yticks(thws)
        ax_dec.set_title("Rolling Style Decisions (Cross-Frequency)", fontsize=16, fontweight='bold')
        ax_dec.legend(loc='lower left', ncol=3, fontsize='small', framealpha=0.9)
        ax_dec.grid(True, alpha=0.3)

        ax_h = fig.add_subplot(gs[-1, 2])
        pivot = np.zeros((len(wns), len(thws)))
        for i, wn in enumerate(wns):
            for j, thw in enumerate(thws):
                res = next(r for r in sweep_results if r['thw'] == thw and r['wn'] == wn)
                pivot[i, j] = res['mae']
        sns.heatmap(pivot, annot=True, fmt=".3f", cmap="YlOrRd_r", ax=ax_h, xticklabels=thws, yticklabels=wns)
        ax_h.set_title("Global Param Sensitivity Heatmap")

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Professional Diagnostics saved to: {save_path}")

    def plot_batch_results(self, df: pd.DataFrame, save_dir: str = None):
        if save_dir is None: save_dir = self.output_dir
        os.makedirs(save_dir, exist_ok=True)
        if "gt_style" in df.columns and "identified_style" in df.columns:
            self._plot_confusion_matrix(df, save_dir)
            self._plot_style_distribution(df, save_dir)

    def _plot_confusion_matrix(self, df: pd.DataFrame, save_dir: str):
        plt.figure(figsize=(10, 8))
        y_true, y_pred = df["gt_style"].astype(str), df["identified_style"].astype(str)
        labels = sorted(list(set(y_true.unique()) | set(y_pred.unique())))
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        sns.heatmap(cm / cm.sum(axis=1)[:, np.newaxis], annot=True, fmt=".1%", cmap="Blues", xticklabels=labels, yticklabels=labels)
        plt.savefig(os.path.join(save_dir, "confusion_matrix.png"))
        plt.close()

    def _plot_style_distribution(self, df: pd.DataFrame, save_dir: str):
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=df, x="gt_style", y="identified_style", hue="gt_style")
        plt.savefig(os.path.join(save_dir, "style_distribution.png"))
        plt.close()
