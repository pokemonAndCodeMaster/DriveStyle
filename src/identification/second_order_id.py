import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.domain.interfaces import BaseIdentifier
from src.domain.models import CarFollowingSegment

class SecondOrderStyleIdentifier(BaseIdentifier):
    """
    基于二阶控制理论与物理约束的前馈跟车风格辨识器 (V9.1 物理一致性校准版)
    """
    def __init__(self, 
                 styles_config: Dict[float, Dict[str, float]] = None,
                 window_size: int = 100, 
                 dt: float = 0.1, 
                 d0: float = 5.0, 
                 jerk_max: float = 2.5, 
                 a_max: float = 3.0, 
                 a_min: float = -5.0,
                 zeta: float = 1.0):
        
        if styles_config is None:
            self.styles_config = {1.0: {'wn': 1.0}, 1.5: {'wn': 0.6}, 2.0: {'wn': 0.4}}
        else:
            self.styles_config = styles_config
            
        self.window_size = window_size
        self.dt = dt
        self.d0 = d0
        self.jerk_max = jerk_max
        self.a_max = a_max
        self.a_min = a_min
        self.zeta = zeta
        
        self.params = {}
        for thw, conf in self.styles_config.items():
            wn = conf.get('wn', 0.6)
            denom = 1 + 2 * self.zeta * wn * thw
            self.params[thw] = {
                'tau': thw / denom if denom != 0 else 0.001,
                'alpha': 1.0 / denom,
                'Kv': (2 * self.zeta * wn) / denom,
                'Kp': (wn ** 2) / denom,
                'wn': wn
            }

    def simulate_segment(self, segment: CarFollowingSegment, thw: float, wn: float) -> np.ndarray:
        df = segment.to_dataframe()
        N = len(df)
        a_sim = np.zeros(N)
        if N == 0: return a_sim
        
        v_ego = df['ego_velocity'].values
        v_lead = df['lead_velocity'].values
        a_lead = df['lead_acceleration'].values
        dist = df['relative_distance'].values
        
        denom = 1 + 2 * self.zeta * wn * thw
        p = {'tau': thw / denom, 'alpha': 1.0 / denom, 'Kv': (2 * self.zeta * wn) / denom, 'Kp': (wn ** 2) / denom}
        
        a_sim[0] = df['ego_acceleration'].values[0]
        v_tmp, d_tmp = v_ego[0], dist[0]
        
        for t in range(1, N):
            e = d_tmp - (thw * v_tmp + self.d0)
            dv = v_lead[t] - v_tmp
            a_cmd = p['alpha'] * a_lead[t] + p['Kv'] * dv + p['Kp'] * e
            
            a_raw = a_sim[t-1] + (self.dt / p['tau']) * (a_cmd - a_sim[t-1])
            j_lim = np.clip((a_raw - a_sim[t-1]) / self.dt, -self.jerk_max, self.jerk_max)
            a_sim[t] = np.clip(a_sim[t-1] + j_lim * self.dt, self.a_min, self.a_max)
            
            v_tmp += a_sim[t] * self.dt
            d_tmp += (v_lead[t] - v_tmp) * self.dt
            
        return a_sim

    def identify(self, segment: CarFollowingSegment) -> pd.DataFrame:
        df = segment.to_dataframe()
        N = len(df)
        if N < self.window_size: return pd.DataFrame()

        pred_horizon = 20 # 2.0s
        results = []
        step = 1
        
        v_ego, v_lead = df['ego_velocity'].values, df['lead_velocity'].values
        a_ego, a_lead = df['ego_acceleration'].values, df['lead_acceleration'].values
        dist, timestamps = df['relative_distance'].values, df['timestamp'].values
        
        for start_idx in range(0, N - self.window_size + 1, step):
            end_idx = start_idx + self.window_size
            window_rays, window_acc_rays = {}, {} 
            cost, valid_ratio = {}, {}
            
            for thw, p in self.params.items():
                # 1. 成本辨识模拟
                a_sim_w = np.zeros(self.window_size)
                a_sim_w[0] = a_ego[start_idx]
                v_w, d_w = v_ego[start_idx], dist[start_idx]
                valid_count = 0
                
                for t in range(1, self.window_size):
                    idx = start_idx + t
                    e = d_w - (thw * v_w + self.d0)
                    dv = v_lead[idx] - v_w
                    a_cmd = p['alpha'] * a_lead[idx] + p['Kv'] * dv + p['Kp'] * e
                    
                    a_raw = a_sim_w[t-1] + (self.dt / p['tau']) * (a_cmd - a_sim_w[t-1])
                    j_lim = np.clip((a_raw - a_sim_w[t-1]) / self.dt, -self.jerk_max, self.jerk_max)
                    a_sim_w[t] = np.clip(a_sim_w[t-1] + j_lim * self.dt, self.a_min, self.a_max)
                    
                    v_w += a_sim_w[t] * self.dt
                    d_w += (v_lead[idx] - v_w) * self.dt
                    
                    if not ((e < -2.0 and a_cmd < -0.5 and a_ego[idx] > 0.5) or 
                            (e > 2.0 and a_cmd > 0.5 and a_ego[idx] < -0.5)):
                        valid_count += 1

                cost[thw] = np.mean(np.abs(a_ego[start_idx:end_idx] - a_sim_w))
                valid_ratio[thw] = valid_count / (self.window_size - 1)

                # 2. 预测射线推演 (2.0s)
                sim_len = min(pred_horizon, N - start_idx)
                thw_r, acc_r = np.zeros(sim_len), np.zeros(sim_len)
                v_r, d_r, a_p = v_ego[start_idx], dist[start_idx], a_ego[start_idx]
                thw_r[0], acc_r[0] = d_r / max(0.5, v_r), a_p

                for t in range(1, sim_len):
                    idx = start_idx + t
                    e_r = d_r - (thw * v_r + self.d0)
                    dv_r = v_lead[idx] - v_r
                    a_c_r = p['alpha'] * a_lead[idx] + p['Kv'] * dv_r + p['Kp'] * e_r
                    
                    a_raw_r = a_p + (self.dt / p['tau']) * (a_c_r - a_p)
                    j_r = np.clip((a_raw_r - a_p) / self.dt, -self.jerk_max, self.jerk_max)
                    a_curr = np.clip(a_p + j_r * self.dt, self.a_min, self.a_max)
                    
                    v_r += a_curr * self.dt
                    d_r += (v_lead[idx] - v_r) * self.dt
                    thw_r[t], acc_r[t] = d_r / max(0.5, v_r), a_curr
                    a_p = a_curr
                
                window_rays[thw], window_acc_rays[thw] = thw_r, acc_r
                
            best_thw = min(cost, key=cost.get)
            results.append({
                "start_time": timestamps[start_idx],
                "identified_style": best_thw,
                "valid_ratio": valid_ratio[best_thw],
                "rays": window_rays,
                "acc_rays": window_acc_rays,
                **{f"cost_{k}": v for k, v in cost.items()}
            })
            
        return pd.DataFrame(results)
