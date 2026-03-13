import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import confusion_matrix
import os

sns.set_theme(style="whitegrid", context="talk")

def plot_confusion_matrix(df, save_dir="output/figures/"):
    os.makedirs(save_dir, exist_ok=True)
    plt.figure(figsize=(10, 8))
    y_true = df['gt_style'].apply(lambda x: f"{x:.1f}s")
    y_pred = df['identified_style'].apply(lambda x: f"{x:.1f}s")
    labels = sorted(y_true.unique())
    
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    annot = [[f"{cm[i, j]}\n({cm_norm[i, j]:.1%})" for j in range(len(labels))] for i in range(len(labels))]

    sns.heatmap(cm_norm, annot=annot, fmt="", cmap="Blues",
                xticklabels=labels, yticklabels=labels,
                cbar_kws={'label': 'Identification Probability'})
    
    plt.title("Driving Style Identification Performance", pad=20)
    plt.xlabel("Identified Target THW (s)", labelpad=10)
    plt.ylabel("Ground Truth Style (s)", labelpad=10)
    plt.tight_layout()
    
    filepath = os.path.join(save_dir, "confusion_matrix.png")
    plt.savefig(filepath, dpi=300)
    print(f"Saved: {filepath}")
    plt.close()

def plot_scenario_performance(df, save_dir="output/figures/"):
    os.makedirs(save_dir, exist_ok=True)
    df['match'] = (df['identified_style'] == df['gt_style']).astype(int)
    perf = df.groupby(['scenario', 'gt_style'])['match'].mean().reset_index()
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=perf, x='scenario', y='match', hue='gt_style', palette="viridis")
    plt.axhline(y=0.9, color='r', linestyle='--', alpha=0.5, label='90% Goal')
    
    plt.title("Identification Accuracy by Scenario & Style")
    plt.ylabel("Accuracy Rate")
    plt.ylim(0, 1.1)
    plt.legend(title="Target Style (s)", loc='lower right')
    plt.tight_layout()
    
    filepath = os.path.join(save_dir, "scenario_performance.png")
    plt.savefig(filepath, dpi=300)
    print(f"Saved: {filepath}")
    plt.close()

def plot_dynamic_residuals(sim_df, iden_df, scenario_id, save_dir="output/figures/"):
    os.makedirs(save_dir, exist_ok=True)
    sim_data = sim_df[sim_df['scenario_id'] == scenario_id]
    iden_data = iden_df[iden_df['scenario_id'] == scenario_id]
    
    if sim_data.empty: return

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True, 
                                       gridspec_kw={'height_ratios': [1, 1, 1.5]})
    
    ax1.plot(sim_data['timestamp'], sim_data['v_lv']*3.6, color='#E74C3C', lw=2, label='Lead Vehicle')
    ax1.plot(sim_data['timestamp'], sim_data['v_ev']*3.6, color='#3498DB', lw=2, label='Ego Vehicle')
    ax1.fill_between(sim_data['timestamp'], sim_data['v_ev']*3.6, sim_data['v_lv']*3.6, color='gray', alpha=0.1)
    ax1.set_ylabel("Speed (km/h)")
    ax1.legend(loc='upper right')
    ax1.set_title(f"Scenario Analysis: ID {scenario_id} ({sim_data['scenario'].iloc[0]})")
    
    ax2.plot(sim_data['timestamp'], sim_data['thw'], color='#27AE60', lw=2, label='Measured THW')
    gt_style = sim_data['gt_style'].iloc[0]
    ax2.axhline(y=gt_style, color='black', ls='--', alpha=0.7, label=f'GT Style ({gt_style}s)')
    ax2.set_ylabel("THW (s)")
    ax2.set_ylim(0, 4)
    ax2.legend(loc='upper right')
    
    cost_cols = ['cost_1.0', 'cost_1.5', 'cost_2.0']
    colors = ['#F1C40F', '#9B59B6', '#1ABC9C']
    for col, color in zip(cost_cols, colors):
        label = f"Hypothesis: {col.split('_')[1]}s"
        ax3.plot(iden_data['start_time'], iden_data[col], color=color, lw=3, label=label)
    
    for idx, row in iden_data.iterrows():
        winner = row['identified_style']
        win_color = colors[0] if winner == 1.0 else (colors[1] if winner == 1.5 else colors[2])
        ax3.axvspan(row['start_time'], row['start_time']+1.0, color=win_color, alpha=0.1)

    ax3.set_ylabel("Model Residual (Cost)")
    ax3.set_xlabel("Time (s)")
    ax3.legend(loc='upper right', title="Candidates")
    
    plt.tight_layout()
    filepath = os.path.join(save_dir, f"scenario_{scenario_id}_analysis.png")
    plt.savefig(filepath, dpi=300)
    print(f"Saved: {filepath}")
    plt.close()
