# 核心物理与配置模块

本模块负责 DriveStyle 系统的“地基”：全局配置的管理与底层物理步进的一致性保证。

## ⚙️ 配置中心 (ConfigManager)

采用单例模式设计，负责解析 `config/default_config.yaml`。

### 核心配置项说明

| 键路径 | 默认值 | 物理意义 |
|--------|--------|---------|
| `physics.dt` | 0.1 | 离散步进时间步长 (s)。 |
| `physics.d0` | 0.0 | 静止安全距离 (m)，设为 0 可消除 THW 偏移。 |
| `physics.jerk_max` | 2.5 | 最大加加速度限制，决定乘坐舒适度。 |
| `identification.pred_horizon` | 100 | 长程稳态推演的时界 (10s)。 |

### 示例：如何动态调参
无需修改代码，直接编辑 YAML：
```yaml
physics:
  jerk_max: 1.5  # 改为极其丝滑的脚法
  a_max: 2.0     # 限制动力输出
```

## ⚛️ 原子物理步进 (Step Physics)

为了确保 **全局仿真** 与 **滑动辨识射线** 具有完全一致的物理表现，我们重构了 `step_physics` 方法。

### 物理计算流程

1.  **误差感知**：$e = dist - (THW \cdot v + d_0)$
2.  **前馈指令**：$a_{cmd} = \alpha a_{lead} + K_v \Delta v + K_p e$
3.  **时延过滤**：使用一阶惯性环节 $\tau$ 处理指令 $a_{cmd}$。
4.  **硬约束截断**：
    -   计算 $jerk = (a_{raw} - a_{prev}) / dt$
    -   限制 $jerk \in [-J_{max}, J_{max}]$
    -   限制 $a_{final} \in [a_{min}, a_{max}]$
5.  **状态更新**：执行二重积分更新 $v$ 和 $dist$。

### 代码实现追踪 [📄](file://src/identification/second_order_id.py#L50)

```python
def step_physics(self, state, cmd_p, thw_target):
    # 此处逻辑确保了每一帧的积分严丝合缝
    # 彻底消除了 V12.0 之前的物理矛盾
```

---

**章节参考源**
- [src/core/config_manager.py](file://src/core/config_manager.py)
- [src/identification/second_order_id.py](file://src/identification/second_order_id.py)

*由 [Mini-Wiki v3.0.6](https://github.com/trsoliu/mini-wiki) 自动生成 | 2026-03-14*
