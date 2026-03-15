import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from src.domain.interfaces import BaseIdentifier
from src.domain.models import CarFollowingSegment
from src.core.config_manager import ConfigManager

class StyleIdentifier(BaseIdentifier):
    """
    一阶跟车风格辨识器 (1st Order Model)
    基于多宇宙假设检验与物理一致性推演
    """
    def __init__(self, target_thws: Optional[List[float]] = None, window_size: int = 100, lambda_default: float = 1.0):
        self.cfg = ConfigManager()
        self.target_thws = target_thws if target_thws is not None else [1.0, 1.5, 2.0]
        self.window_size = window_size
        self.lambda_default = lambda_default
        self.dt = self.cfg.get('physics.dt', 0.1)
        # 增加预测长度
        self.pred_horizon = self.cfg.get('identification.pred_horizon', 100)

    def step_physics(self, state: Dict[str, float], cmd_p: Dict[str, float], thw_target: float) -> Dict[str, float]:
        """
        一阶物理引擎步进：计算下一时刻的状态
        与二阶接口保持一致。
        """
        dt = cmd_p.get('dt', self.dt)
        lb = cmd_p.get('lambda', 1.0)
        
        d_rel = state['d']
        v_ego = state['v']
        v_lead = state['v_l']
        
        # 避免除以 0
        v_ego_safe = max(v_ego, 0.5)
        thw = d_rel / v_ego_safe
        dv = v_lead - v_ego
        
        # 核心控制律 (一阶)
        # a_ego = dv/thw + lambda * (v/thw) * (thw - thw_ref)
        a_ego = (dv / max(thw, 0.1)) + lb * (v_ego_safe / max(thw, 0.1)) * (thw - thw_target)
        
        # 物理硬约束 (参考二阶模型)
        a_ego = np.clip(a_ego, -5.0, 3.0)
        
        # 状态更新 (欧拉积分)
        v_next = max(v_ego + a_ego * dt, 0.0)
        # 相对距离更新：d_next = d + (v_l - v_ego)*dt - 0.5*a*dt^2 (保持物理一致性)
        d_next = d_rel + (v_lead - v_ego) * dt - 0.5 * a_ego * dt**2
        
        return {
            'a': a_ego, 
            'v': v_next, 
            'd': d_next, 
            'thw': d_next / max(v_next, 0.5),
            'e': thw - thw_target
        }

    def simulate_segment(self, segment: Union[CarFollowingSegment, pd.DataFrame, pd.Series], thw: float, wn: float, zeta: float = 1.0) -> Dict[str, np.ndarray]:
        """
        与二阶模型接口一致。wn 对应 lambda。
        支持从 segment_data 或 window 数据帧中起始。
        """
        if isinstance(segment, CarFollowingSegment):
            df = segment.to_dataframe()
        elif isinstance(segment, pd.Series):
            df = pd.DataFrame([segment]).reset_index(drop=True)
        elif isinstance(segment, pd.DataFrame):
            df = segment.reset_index(drop=True)
        else:
            raise ValueError("Unsupported segment type")
            
        # 这里决定模拟长度
        is_ray = len(df) <= 1 
        N = self.pred_horizon if is_ray else len(df)
        
        res = {'acc': np.zeros(N), 'v': np.zeros(N), 'thw': np.zeros(N)}
        if df.empty: return res
        
        # 初始状态提取
        v_col = 'ego_velocity' if 'ego_velocity' in df.columns else 'v_ev'
        d_col = 'relative_distance' if 'relative_distance' in df.columns else 'dist'
        vl_col = 'lead_velocity' if 'lead_velocity' in df.columns else 'v_lv'
        
        state = {
            'v': df[v_col].iloc[0], 
            'd': df[d_col].iloc[0], 
            'v_l': df[vl_col].iloc[0]
        }
        
        cmd_p = {'lambda': wn, 'dt': self.dt}
        
        for t in range(N):
            # 如果是随动模拟 (Data Following)，更新前车速度；如果是预测射线 (Ray Casting)，假设前车匀速
            if not is_ray and t < len(df):
                state['v_l'] = df[vl_col].iloc[t]
            
            out = self.step_physics(state, cmd_p, thw)
            res['acc'][t], res['v'][t], res['thw'][t] = out['a'], out['v'], out['thw']
            state['v'], state['d'] = out['v'], out['d']
            
        return res

    def identify(self, segment: CarFollowingSegment) -> pd.DataFrame:
        """
        辨识主流程：保持原有高效计算逻辑，但更新 rays 生成部分以匹配新接口。
        """
        df = segment.to_dataframe()
        if df.empty or len(df) < self.window_size:
            return pd.DataFrame()

        df = df.copy()
        df['v_ev'] = df['ego_velocity']
        df['v_lv'] = df['lead_velocity']
        df['dist'] = df['relative_distance']
        df['a_ev'] = df['ego_acceleration']
        df['dv'] = df['lead_velocity'] - df['ego_velocity']
        df['thw_obs'] = df['dist'] / df['v_ev'].clip(lower=0.5)
        
        # 剥离随动基线
        df['a_base_calc'] = df['dv'] / df['thw_obs'].clip(lower=0.1)
        df['f_actual'] = df['a_ev'] - df['a_base_calc']
        
        results = []
        step = max(1, self.window_size // 5)
        
        for i in range(0, len(df) - self.window_size + 1, step):
            window = df.iloc[i : i + self.window_size]
            costs = {}
            valid_mask_counts = {}
            rays = {}
            acc_rays = {}
            
            for thw_k in self.target_thws:
                # A. 向量化计算成本 (保持效率)
                f_ideal_k = self.lambda_default * (window['v_ev'] / window['thw_obs'].clip(lower=0.1)) * (window['thw_obs'] - thw_k)
                residual = (window['f_actual'] - f_ideal_k).abs()
                costs[thw_k] = residual.mean()
                
                # B. 意图校验
                error = window['thw_obs'] - thw_k
                valid_mask = (window['f_actual'] * error >= -0.1)
                valid_mask_counts[thw_k] = valid_mask.mean()
                
                # C. 生成射线 (调用新接口)
                sim_res = self.simulate_segment(window.iloc[0:1], thw_k, self.lambda_default)
                rays[thw_k] = sim_res['thw']
                acc_rays[thw_k] = sim_res['acc']

            best_thw = min(costs, key=costs.get)
            
            res_item = {
                "start_time": window['timestamp'].iloc[0],
                "end_time": window['timestamp'].iloc[-1],
                "identified_style": best_thw,
                "valid_ratio": valid_mask_counts[best_thw],
                "rays": rays,
                "acc_rays": acc_rays,
            }
            for thw_k, c in costs.items():
                res_item[f"cost_{thw_k}"] = c
            
            results.append(res_item)
            
        return pd.DataFrame(results)
