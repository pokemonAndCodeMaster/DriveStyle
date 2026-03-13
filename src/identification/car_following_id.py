import pandas as pd
import numpy as np

class StyleIdentifier:
    """
    基于多宇宙假设检验的跟车风格辨识器
    """
    def __init__(self, target_thws=[1.0, 1.5, 2.0], window_size=150, lambda_default=1.0):
        self.target_thws = target_thws
        self.window_size = window_size
        self.lambda_default = lambda_default

    def identify(self, df):
        """
        输入单段轨迹数据，输出窗口级的辨识结果
        """
        # 1. 基础物理量计算
        df = df.copy()
        df['dv'] = df['v_lv'] - df['v_ev']
        df['thw_obs'] = df['dist'] / df['v_ev'].clip(lower=0.5)
        
        # 2. 剥离随动基线：实际纠偏力 = 实际加速度 - 随动基线
        df['a_base_calc'] = df['dv'] / df['thw_obs'].clip(lower=0.1)
        df['f_actual'] = df['a_ev'] - df['a_base_calc']
        
        results = []
        # 3. 滑动窗口积分
        for i in range(0, len(df) - self.window_size, 50): # 窗口平移步长50
            window = df.iloc[i : i + self.window_size].copy()
            costs = {}
            valid_mask_counts = {}
            
            # 多模型残差计算
            for thw_k in self.target_thws:
                # 该假设目标下的理想纠偏力
                window['f_ideal_k'] = self.lambda_default * (window['v_ev'] / window['thw_obs'].clip(lower=0.1)) * (window['thw_obs'] - thw_k)
                # 残差绝对值积分
                window['residual'] = (window['f_actual'] - window['f_ideal_k']).abs()
                costs[thw_k] = window['residual'].mean()
                
                # 意图方向校验 (排除动力学限幅导致的脏数据)
                error = window['thw_obs'] - thw_k
                valid_mask = (window['f_actual'] * error >= -0.1)
                valid_mask_counts[thw_k] = valid_mask.mean()

            # 赢家通吃：选择残差最小的模型作为辨识结果
            best_thw = min(costs, key=costs.get)
            
            results.append({
                "start_time": window['timestamp'].iloc[0],
                "identified_style": best_thw,
                "cost_1.0": costs[1.0],
                "cost_1.5": costs[1.5],
                "cost_2.0": costs[2.0],
                "valid_ratio": valid_mask_counts[best_thw],
                "gt_style": window['gt_style'].iloc[0],
                "scenario": window['scenario'].iloc[0]
            })
            
        return pd.DataFrame(results)
