class FollowerController:
    """
    基于误差跟踪模型的驾驶员仿真控制器
    模拟不同风格的跟车行为
    """
    def __init__(self, thw_k, lambda_gain=None, dt=0.02):
        self.thw_k = thw_k
        # 自动匹配纠偏增益：激进者(更小THW)往往倾向于更大的纠偏力度
        if lambda_gain is None:
            if thw_k <= 1.0: self.lambda_gain = 1.5   # 激进 Aggressive
            elif thw_k >= 2.0: self.lambda_gain = 0.6 # 保守 Conservative
            else: self.lambda_gain = 1.0              # 普通 Normal
        else:
            self.lambda_gain = lambda_gain
        self.dt = dt

    def compute_acceleration(self, v_ego, v_lead, distance):
        """
        核心物理公式：a_cmd = a_base + a_correction
        """
        thw = distance / max(v_ego, 0.5)
        dv = v_lead - v_ego
        
        # 1. 随动基线：维持当前THW所需的物理加速度 (被动跟随)
        a_base = dv / max(thw, 0.1)
        
        # 2. 主动纠偏力：向目标THW靠近的“弹簧拉力” (主观意图)
        a_correction = self.lambda_gain * (max(v_ego, 1.0) / max(thw, 0.1)) * (thw - self.thw_k)
        
        a_cmd = a_base + a_correction
        return a_cmd, a_base, a_correction
