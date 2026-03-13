import numpy as np

class Vehicle:
    """
    高保真车辆动力学模型：包含一阶惯性滞后、Jerk限制和物理硬约束
    """
    def __init__(self, x0, v0, a_max=2.5, a_min=-5.0, tau=0.3, jerk_max=5.0, dt=0.02):
        self.x = x0
        self.v = v0
        self.a = 0.0
        self.a_cmd = 0.0
        
        # 物理限制
        self.a_max = a_max
        self.a_min = a_min
        self.tau = tau          # 执行器时间常数 (s)
        self.jerk_max = jerk_max # 最大加加速度 (m/s^3)
        self.dt = dt

    def update(self, a_cmd_target):
        # 1. 考虑Jerk限制的指令平滑
        a_cmd_clamped = np.clip(a_cmd_target, self.a_min, self.a_max)
        
        # 2. 一阶惯性模拟响应延迟 (动力学响应)
        da = (a_cmd_clamped - self.a) / self.tau
        da_limited = np.clip(da, -self.jerk_max, self.jerk_max)
        
        self.a += da_limited * self.dt
        
        # 3. 状态更新 (运动学)
        self.v += self.a * self.dt
        if self.v < 0: 
            self.v = 0
            self.a = 0
        self.x += self.v * self.dt

    def get_state(self):
        return {"x": self.x, "v": self.v, "a": self.a}
