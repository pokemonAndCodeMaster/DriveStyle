import numpy as np

class LeadVehicleProfile:
    """
    定义前车动作轨迹，模拟各种复杂的现实工况
    """
    def __init__(self, v0, duration, dt=0.02):
        self.v0 = v0
        self.duration = duration
        self.dt = dt
        self.timesteps = int(duration / dt)
        self.v_profile = np.full(self.timesteps, v0, dtype=float)
        self.x_profile = np.zeros(self.timesteps)

    def constant_speed(self):
        return self._generate_x()

    def step_braking(self, start_time, decel=-3.0):
        start_idx = int(start_time / self.dt)
        for i in range(start_idx, self.timesteps):
            new_v = self.v_profile[i-1] + decel * self.dt
            self.v_profile[i] = max(0, new_v)
        return self._generate_x()

    def emergency_braking(self, start_time=5.0):
        return self.step_braking(start_time, decel=-6.0)

    def slow_acceleration(self, start_time=5.0, accel=1.5):
        start_idx = int(start_time / self.dt)
        for i in range(start_idx, self.timesteps):
            new_v = self.v_profile[i-1] + accel * self.dt
            self.v_profile[i] = min(40, new_v) # 最高速限制
        return self._generate_x()

    def sine_wave(self, amplitude=3.0, frequency=0.1):
        t = np.arange(0, self.duration, self.dt)
        v = self.v0 + amplitude * np.sin(2 * np.pi * frequency * t)
        self.v_profile = np.clip(v, 2.0, 45.0)
        return self._generate_x()

    def _generate_x(self):
        self.x_profile = np.cumsum(self.v_profile) * self.dt
        return self.v_profile, self.x_profile

def generate_scenario_configs():
    """
    生成大规模仿真矩阵：笛卡尔积覆盖各类工况
    """
    configs = []
    speeds = [15.0, 25.0, 35.0]  # 初始速度
    thw_inits = [1.2, 1.8, 2.8]  # 初始距离对应时距
    target_styles = [1.0, 1.5, 2.0] # 待辨识风格目标
    actions = ["constant", "braking", "emergency", "accel", "sine"]
    
    for v in speeds:
        for thw_init in thw_inits:
            for style in target_styles:
                for act in actions:
                    configs.append({
                        "v_lv": v, 
                        "v_ev": v, 
                        "d_init": v * thw_init, 
                        "style_k": style, 
                        "action": act
                    })
    return configs
