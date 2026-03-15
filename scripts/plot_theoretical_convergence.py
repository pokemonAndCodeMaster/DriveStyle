import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def second_order_response(t, wn, z, e0=1.0):
    if z < 1:
        wd = wn * np.sqrt(1 - z**2)
        return e0 * np.exp(-z * wn * t) * (np.cos(wd * t) + (z / np.sqrt(1 - z**2)) * np.sin(wd * t))
    elif z == 1:
        return e0 * np.exp(-wn * t) * (1 + wn * t)
    else:
        w_h = wn * np.sqrt(z**2 - 1)
        return e0 * np.exp(-z * wn * t) * (np.cosh(w_h * t) + (z / np.sqrt(z**2 - 1)) * np.sinh(w_h * t))

def first_order_response(t, lam, e0=1.0):
    return e0 * np.exp(-lam * t)

def find_first_crossing(t, e_t, threshold=0.1):
    indices = np.where(e_t <= threshold)[0]
    if len(indices) > 0:
        return t[indices[0]]
    return None

def plot_theoretical_convergence():
    sns.set_theme(style='whitegrid', context='talk')
    t = np.linspace(0, 15, 1000)
    e0 = 1.0
    
    # Create 3 subplots: 1st order, 2nd order (wn), 2nd order (zeta)
    fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(28, 8), sharey=True)
    
    # --- 1. First-order Model ---
    lam_list = [0.2, 0.5, 1.0]
    colors0 = sns.color_palette('rocket', len(lam_list))
    for lam, color in zip(lam_list, colors0):
        e_t = first_order_response(t, lam, e0)
        ax0.plot(t, e_t, label=rf'$\lambda = {lam}$', linewidth=3, color=color)
        t_settle = -np.log(0.1)/lam
        if t_settle < 15:
            ax0.scatter([t_settle], [0.1], color=color, s=80, zorder=5)
    ax0.axhline(0.1, color='gray', linestyle='--', alpha=0.5)
    ax0.set_title('First-order Model:\nPure Exponential Decay', fontsize=20, fontweight='bold')
    ax0.set_xlabel('Time (s)', fontsize=16)
    ax0.set_ylabel('Error Ratio $e(t)/e(0)$', fontsize=16)
    ax0.legend(fontsize=12)
    ax0.set_ylim(-0.3, 1.1)

    # --- 2. Second-order: Effect of wn ---
    zeta_fixed = 0.7
    wn_list = [0.5, 1.0, 2.0]
    colors1 = sns.color_palette('flare', len(wn_list))
    for wn, color in zip(wn_list, colors1):
        e_t = second_order_response(t, wn, zeta_fixed, e0)
        ax1.plot(t, e_t, label=rf'$\omega_n = {wn}, \zeta = {zeta_fixed}$', linewidth=3, color=color)
        t_90 = find_first_crossing(t, e_t, 0.1)
        if t_90:
            ax1.scatter([t_90], [0.1], color=color, s=80, zorder=5)
            ax1.annotate(f'{t_90:.1f}s', (t_90, 0.1), textcoords='offset points', xytext=(0, 10), ha='center', fontsize=12, color=color, fontweight='bold')
    ax1.axhline(0.1, color='gray', linestyle='--', alpha=0.5)
    ax1.set_title(f'Second-order: Effect of $\omega_n$\n(Fixed $\zeta = {zeta_fixed}$)', fontsize=20, fontweight='bold')
    ax1.set_xlabel('Time (s)', fontsize=16)
    ax1.legend(fontsize=12)
    ax1.set_ylim(-0.3, 1.1)

    # --- 3. Second-order: Effect of zeta ---
    wn_fixed = 1.0
    zeta_list = [0.5, 0.7, 1.0, 1.5]
    colors2 = sns.color_palette('viridis', len(zeta_list))
    for z, color in zip(zeta_list, colors2):
        e_t = second_order_response(t, wn_fixed, z, e0)
        ax2.plot(t, e_t, label=rf'$\zeta = {z}, \omega_n = {wn_fixed}$', linewidth=3, color=color)
        if z < 1.0:
            peak_idx = np.argmin(e_t)
            if e_t[peak_idx] < 0:
                os_percent = abs(e_t[peak_idx]) * 100
                ax2.scatter([t[peak_idx]], [e_t[peak_idx]], color=color, s=80, zorder=5)
                ax2.annotate(f'{os_percent:.1f}% OS', (t[peak_idx], e_t[peak_idx]), textcoords='offset points', xytext=(0, -20), ha='center', fontsize=12, color=color, fontweight='bold')
    ax2.axhline(0, color='black', linestyle='-', alpha=0.3)
    ax2.set_title(f'Second-order: Effect of $\zeta$\n(Fixed $\omega_n = {wn_fixed}$)', fontsize=20, fontweight='bold')
    ax2.set_xlabel('Time (s)', fontsize=16)
    ax2.legend(fontsize=12)
    ax2.set_ylim(-0.3, 1.1)
    
    output_dir = '/home/yyh/projects/DriveStyle/output/figures/'
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, 'theoretical_convergence.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f'[SUCCESS] Updated theoretical convergence plot (3 panels) saved to {save_path}')

if __name__ == "__main__":
    plot_theoretical_convergence()
