import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.domain.interfaces import BaseIdentifier
from src.domain.models import CarFollowingSegment
from src.core.config_manager import ConfigManager

class SecondOrderStyleIdentifier(BaseIdentifier):
    """
    重构后的二阶辨识器：完全参数化，逻辑解耦。
    """
    def __init__(self, config: Dict[float, Dict[str, float]] = None, **kwargs):
        self.cfg = ConfigManager()
        
        # 物理限制从配置中加载
        self.dt = self.cfg.get('physics.dt', 0.1)
        self.d0 = self.cfg.get('physics.d0', 0.0)
        self.jerk_max = self.cfg.get('physics.jerk_max', 2.5)
        self.a_max = self.cfg.get('physics.a_max', 3.0)
        self.a_min = self.cfg.get('physics.a_min', -5.0)
        
        # 辨识配置
        self.window_size = kwargs.get('window_size', self.cfg.get('identification.window_size_default', 100))
        self.pred_horizon = self.cfg.get('identification.pred_horizon', 100)
        
        # 初始化风格矩阵
        self.styles_config = config or self._get_default_styles()
        self.params = self._precompute_params()

    def _get_default_styles(self):
        # 从配置中构造默认风格组合
        thws = self.cfg.get('identification.targets.thw')
        wns = self.cfg.get('identification.targets.wn')
        # 默认匹配 (这里可以根据业务逻辑调整)
        return {t: {'wn': 0.8, 'zeta': 1.0} for t in thws}

    def _precompute_params(self):
        params = {}
        for thw, conf in self.styles_config.items():
            wn = conf.get('wn', 0.8)
            zeta = conf.get('zeta', 1.0)
            denom = 1 + 2 * zeta * wn * thw
            params[thw] = {
                'tau': thw / denom if denom != 0 else 0.001,
                'alpha': 1.0 / denom,
                'Kv': (2 * zeta * wn) / denom,
                'Kp': (wn ** 2) / denom,
                'wn': wn, 'zeta': zeta
            }
        return params

    def step_physics(self, state: Dict[str, float], cmd_p: Dict[str, float], thw_target: float) -> Dict[str, float]:
        """
        核心物理步进逻辑：解耦单帧计算，确保多处复用一致性。
        """
        e = state['d'] - (thw_target * state['v'] + self.d0)
        dv = state['v_l'] - state['v']
        
        # 指令生成
        a_cmd = cmd_p['alpha'] * state['a_l'] + cmd_p['Kv'] * dv + cmd_p['Kp'] * e
        
        # 延迟与硬约束
        a_raw = state['a_prev'] + (self.dt / cmd_p['tau']) * (a_cmd - state['a_prev'])
        j_lim = np.clip((a_raw - state['a_prev']) / self.dt, -self.jerk_max, self.jerk_max)
        a_curr = np.clip(state['a_prev'] + j_lim * self.dt, self.a_min, self.a_max)
        
        # 积分
        v_next = state['v'] + a_curr * self.dt
        d_next = state['d'] + (state['v_l'] - v_next) * self.dt
        
        return {'a': a_curr, 'v': v_next, 'd': d_next, 'e': e, 'a_cmd': a_cmd}

    def simulate_segment(self, segment: CarFollowingSegment, thw: float, wn: float, zeta: float = 1.0) -> Dict[str, np.ndarray]:
        df = segment.to_dataframe()
        N = len(df)
        res = {'acc': np.zeros(N), 'v': np.zeros(N), 'thw': np.zeros(N)}
        if N == 0: return res
        
        # 初始化状态
        state = {'v': df['ego_velocity'].iloc[0], 'd': df['relative_distance'].iloc[0], 
                 'a_prev': df['ego_acceleration'].iloc[0], 'v_l': df['lead_velocity'].iloc[0], 'a_l': df['lead_acceleration'].iloc[0]}
        
        denom = 1 + 2 * zeta * wn * thw
        cmd_p = {'tau': thw / denom, 'alpha': 1.0 / denom, 'Kv': (2 * zeta * wn) / denom, 'Kp': (wn ** 2) / denom}
        
        for t in range(N):
            state['v_l'] = df['lead_velocity'].iloc[t]
            state['a_l'] = df['lead_acceleration'].iloc[t]
            out = self.step_physics(state, cmd_p, thw)
            res['acc'][t], res['v'][t] = out['a'], out['v']
            res['thw'][t] = out['d'] / max(0.5, out['v'])
            state['v'], state['d'], state['a_prev'] = out['v'], out['d'], out['a']
            
        return res

    def identify(self, segment: CarFollowingSegment) -> pd.DataFrame:
        df = segment.to_dataframe()
        N = len(df)
        if N < self.window_size: return pd.DataFrame()
        
        results = []
        for start_idx in range(0, N - self.window_size + 1, 1):
            window_rays, window_acc_rays, cost, valid_ratio = {}, {}, {}, {}
            
            for thw, p in self.params.items():
                # 1. 成本计算 (固定窗口)
                a_sim_w = np.zeros(self.window_size)
                state = {'v': df['ego_velocity'].iloc[start_idx], 'd': df['relative_distance'].iloc[start_idx], 
                         'a_prev': df['ego_acceleration'].iloc[start_idx]}
                v_arr, d_arr, a_arr = df['ego_velocity'].values, df['relative_distance'].values, df['ego_acceleration'].values
                v_l_arr, a_l_arr = df['lead_velocity'].values, df['lead_acceleration'].values
                
                valid_count = 0
                for t in range(self.window_size):
                    idx = start_idx + t
                    state['v_l'], state['a_l'] = v_l_arr[idx], a_l_arr[idx]
                    out = self.step_physics(state, p, thw)
                    a_sim_w[t] = out['a']
                    state['v'], state['d'], state['a_prev'] = out['v'], out['d'], out['a']
                    # 方向一致性校验
                    if not ((out['e'] < -2.0 and out['a_cmd'] < -0.5 and a_arr[idx] > 0.5) or 
                            (out['e'] > 2.0 and out['a_cmd'] > 0.5 and a_arr[idx] < -0.5)):
                        valid_count += 1

                cost[thw] = np.mean(np.abs(a_arr[start_idx:start_idx+self.window_size] - a_sim_w))
                valid_ratio[thw] = valid_count / self.window_size

                # 2. 长程推演 (10s)
                thw_r, acc_r = [], []
                state_r = {'v': v_arr[start_idx], 'd': d_arr[start_idx], 'a_prev': a_arr[start_idx]}
                for t in range(self.pred_horizon):
                    idx = min(start_idx + t, N - 1)
                    state_r['v_l'], state_r['a_l'] = v_l_arr[idx], a_l_arr[idx]
                    out = self.step_physics(state_r, p, thw)
                    thw_r.append(out['d']/max(0.5, out['v'])); acc_r.append(out['a'])
                    state_r['v'], state_r['d'], state_r['a_prev'] = out['v'], out['d'], out['a']
                    if t > 30 and abs(out['e']) < 0.05: break
                window_rays[thw], window_acc_rays[thw] = np.array(thw_r), np.array(acc_r)

            best_thw = min(cost, key=cost.get)
            results.append({
                "start_time": df['timestamp'].iloc[start_idx], "identified_style": best_thw,
                "valid_ratio": valid_ratio[best_thw], "rays": window_rays, "acc_rays": window_acc_rays,
                **{f"cost_{k}": v for k, v in cost.items()}
            })
        return pd.DataFrame(results)
