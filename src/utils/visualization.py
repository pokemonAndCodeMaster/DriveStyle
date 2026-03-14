import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from typing import Any, List, Union
from sklearn.metrics import confusion_matrix
from src.domain.interfaces import BaseVisualizer
from src.domain.models import CarFollowingSegment

class MatplotlibVisualizer(BaseVisualizer):
    """
    Matplotlib-based visualizer for car-following analysis.
    """
    
    def __init__(self, style: str = "whitegrid", context: str = "talk"):
        sns.set_theme(style=style, context=context)
        self.output_dir = "output/figures/"
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_results(self, data: Any, output_path: str = None):
        """
        Generic entry point for plotting as per interface.
        Dispatches based on data type.
        """
        if isinstance(data, CarFollowingSegment):
            self.plot_segment(data, output_path)
        elif isinstance(data, pd.DataFrame):
            self.plot_batch_results(data, output_path)
        else:
            print(f"Unsupported data type for visualization: {type(data)}")

    def plot_segment(self, segment: CarFollowingSegment, id_results: pd.DataFrame = None, save_path: str = None):
        """
        Visualizes a single car-following segment dynamic variables and identification results.
        """
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"segment_{segment.segment_id}.png")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        ego_states = segment.ego_vehicle.states
        times = np.array([s.timestamp for s in ego_states])
        v_ego = segment.ego_vehicle.get_velocities()
        v_target = segment.target_vehicle.get_velocities()
        a_ego = segment.ego_vehicle.get_accelerations()
        dist = segment.relative_distance
        thw_obs = np.where(v_ego > 0.1, dist / v_ego, np.nan)

        rows = 4 if id_results is None or id_results.empty else 5
        fig, axes = plt.subplots(rows, 1, figsize=(14, 4 * rows), sharex=True)
        if rows == 1: axes = [axes]

        # Panel 0: Velocity
        sns.lineplot(x=times, y=v_target * 3.6, ax=axes[0], color='red', label="Lead Vel (km/h)")
        sns.lineplot(x=times, y=v_ego * 3.6, ax=axes[0], color='blue', label="Ego Vel (km/h)")
        axes[0].set_ylabel("Velocity")
        axes[0].set_title(f"Segment: {segment.segment_id} | Target: {segment.target_id}")

        # Panel 1: Distance & THW
        ax1_twin = axes[1].twinx()
        sns.lineplot(x=times, y=dist, ax=axes[1], color='green', label="Distance (m)")
        sns.lineplot(x=times, y=thw_obs, ax=ax1_twin, color='black', alpha=0.3, label="Observed THW (s)")
        axes[1].set_ylabel("Distance (m)")
        ax1_twin.set_ylabel("THW (s)")
        ax1_twin.set_ylim(0, 5)

        # Panel 2: Acceleration & Reference Styles
        sns.lineplot(x=times, y=a_ego, ax=axes[2], color='purple', linewidth=2.5, label="Actual Accel", zorder=5)
        
        # Calculate Reference Accel for comparison
        # f_ideal_k = lambda * (v_ev / thw_obs) * (thw_obs - thw_k)
        # a_ideal_k = f_ideal_k + a_base, where a_base = (v_lv - v_ev) / thw_obs
        dv = v_target - v_ego
        thw_safe = np.clip(thw_obs, 0.1, 10.0)
        a_base = dv / thw_safe
        
        styles = [1.0, 1.5, 2.0]
        colors = ['red', 'orange', 'green']
        for s, c in zip(styles, colors):
            f_ideal = 1.0 * (v_ego / thw_safe) * (thw_obs - s)
            a_ideal = f_ideal + a_base
            axes[2].plot(times, a_ideal, color=c, linestyle='--', alpha=0.4, label=f"Ref Accel ({s}s)")
        
        axes[2].set_ylabel("Accel (m/s²)")
        axes[2].legend(loc="upper right", fontsize='x-small', ncol=2)

        if rows == 5:
            # Panel 3: Identification Costs
            cost_cols = [c for c in id_results.columns if c.startswith('cost_')]
            for col in cost_cols:
                thw_val = col.replace('cost_', '')
                # Use plot with markers to ensure visibility for single-window results
                axes[3].plot(id_results['start_time'], id_results[col], 'o-', label=f"Cost THW={thw_val}")
            axes[3].set_ylabel("Resid. Cost")
            axes[3].grid(True, which="both", alpha=0.3)
            axes[3].legend(loc='upper right')
            
            # Panel 4: Identified Style (Winner)
            # Use marker for single-point results
            axes[4].step(id_results['start_time'], id_results['identified_style'], where='post', color='darkblue', linewidth=2, label="Identified Style", marker='s')
            
            if 'gt_style' in id_results.columns and not id_results['gt_style'].isna().all():
                axes[4].axhline(y=id_results['gt_style'].iloc[0], color='red', linestyle='--', alpha=0.6, label="GT Style")
            
            axes[4].set_ylabel("Style (THW)")
            axes[4].set_ylim(0.5, 2.5)
            axes[4].legend(loc='upper right')
        else:
            # If no ID results, use panel 3 for THW detail
            sns.lineplot(x=times, y=thw_obs, ax=axes[3], color='black', label="Observed THW")
            axes[3].set_ylabel("THW (s)")
            axes[3].set_ylim(0, 5)

        axes[-1].set_xlabel("Time (s)")
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"Segment plot saved to: {save_path}")

    def plot_batch_results(self, df: pd.DataFrame, save_dir: str = None):
        if save_dir is None:
            save_dir = self.output_dir
        os.makedirs(save_dir, exist_ok=True)

        if "gt_style" in df.columns and "identified_style" in df.columns:
            self._plot_confusion_matrix(df, save_dir)
            self._plot_style_distribution(df, save_dir)

        if "scenario" in df.columns and "gt_style" in df.columns and "identified_style" in df.columns:
            self._plot_scenario_performance(df, save_dir)

    def _plot_confusion_matrix(self, df: pd.DataFrame, save_dir: str):
        plt.figure(figsize=(10, 8))
        y_true = df["gt_style"].astype(str)
        y_pred = df["identified_style"].astype(str)
        labels = sorted(list(set(y_true.unique()) | set(y_pred.unique())))
        
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
        
        annot = [[f"{cm[i, j]}\n({cm_norm[i, j]:.1%})" for j in range(len(labels))] for i in range(len(labels))]

        sns.heatmap(cm_norm, annot=annot, fmt="", cmap="Blues",
                    xticklabels=labels, yticklabels=labels,
                    cbar_kws={"label": "Identification Probability"})
        
        plt.title("Driving Style Identification Performance", pad=20)
        plt.xlabel("Identified Style (s)", labelpad=10)
        plt.ylabel("Ground Truth Style (s)", labelpad=10)
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "confusion_matrix.png"), dpi=300)
        plt.close()

    def _plot_scenario_performance(self, df: pd.DataFrame, save_dir: str):
        df = df.copy()
        df["match"] = (df["identified_style"] == df["gt_style"]).astype(int)
        perf = df.groupby(["scenario", "gt_style"])["match"].mean().reset_index()
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=perf, x="scenario", y="match", hue="gt_style")
        plt.axhline(y=0.9, color="r", linestyle="--", alpha=0.5, label="90% Goal")
        plt.title("Identification Accuracy by Scenario & Style")
        plt.ylabel("Accuracy Rate")
        plt.ylim(0, 1.1)
        plt.legend(title="Target Style (s)", loc="lower right")
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "scenario_performance.png"), dpi=300)
        plt.close()

    def _plot_style_distribution(self, df: pd.DataFrame, save_dir: str):
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=df, x="gt_style", y="identified_style", hue="gt_style", palette="Set2")
        sns.stripplot(data=df, x="gt_style", y="identified_style", color=".3", alpha=0.4)
        plt.title("Distribution of Identified Styles")
        plt.xlabel("Ground Truth Style (s)")
        plt.ylabel("Identified Style (s)")
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "style_distribution_box.png"), dpi=300)
        plt.close()
