import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def second_order_response(wn, zeta, t):
    """
    Calculate the step response of a second-order system:
    G(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
    """
    num = [wn**2]
    den = [1, 2*zeta*wn, wn**2]
    sys = signal.TransferFunction(num, den)
    t, y = signal.step(sys, T=t)
    return t, y

def run_comparison():
    t = np.linspace(0, 20, 1000)
    
    plt.figure(figsize=(15, 6))

    # 1. Effect of Natural Frequency (wn) - Speed of Response
    plt.subplot(1, 2, 1)
    wn_list = [0.5, 1.0, 2.0]
    zeta_base = 0.7
    for wn in wn_list:
        t_res, y_res = second_order_response(wn, zeta_base, t)
        plt.plot(t_res, y_res, label=f'wn={wn}, zeta={zeta_base}')
    
    plt.title('Effect of Natural Frequency (wn) on Speed\n(Fixed zeta=0.7)')
    plt.xlabel('Time (s)')
    plt.ylabel('Response')
    plt.grid(True)
    plt.legend()

    # 2. Effect of Damping Ratio (zeta) - Overshoot/Stability
    plt.subplot(1, 2, 2)
    zeta_list = [0.3, 0.7, 1.2]
    wn_base = 1.0
    for zeta in zeta_list:
        t_res, y_res = second_order_response(wn_base, zeta, t)
        plt.plot(t_res, y_res, label=f'wn={wn_base}, zeta={zeta}')
    
    plt.title('Effect of Damping Ratio (zeta) on Overshoot\n(Fixed wn=1.0)')
    plt.xlabel('Time (s)')
    plt.ylabel('Response')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    output_path = '/home/yyh/projects/DriveStyle/output/figures/second_order_dynamics_demo.png'
    plt.savefig(output_path)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_comparison()
