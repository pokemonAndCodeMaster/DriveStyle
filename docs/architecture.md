# DriveStyle 架构设计文档

## 1. 设计哲学
DriveStyle 遵循 **“高内聚、低耦合、可扩展”** 的现代软件工程架构。系统的核心目标是将底层的**物理模拟**与上层的**算法辨识**完全解耦，使得研究人员可以独立地替换动力学模型或升级辨识算法，而无需重写整个 Pipeline。

## 2. 目录层级规范

```text
DriveStyle/
├── docs/                       # 核心文档库
├── src/                        # 核心源代码 (Package)
│   ├── core/                   # 基础设施层：车辆动力学 (Vehicle)、控制基类
│   ├── scenarios/              # 场景定义层：跟车、变道等具体工况生成器
│   ├── identification/         # 算法解析层：各场景的风格辨识器实现
│   └── utils/                  # 工具层：指标计算、可视化绘图
├── scripts/                    # 执行入口：串联 src/ 各模块的 Pipeline
├── output/                     # 产出物归档：数据 (.csv) 与分析图表 (.png)
└── tests/                      # 单元测试用例
```

## 3. 核心模块交互 (Data Flow)

1. **`src.scenarios`** 负责根据配置生成前车 (Lead Vehicle) 的动作轨迹（如匀速、急刹、正弦波动）。
2. **`src.core`** 中的 `Vehicle` 和 `FollowerController` 根据前车状态，模拟出带有特定风格偏好且受物理约束的自车 (Ego Vehicle) 响应，并将状态压入记录列表。
3. 仿真结果流转到 **`src.identification`**。辨识器接收一段“黑盒”时序数据，不知道自车的底层参数，仅通过“剥离随动基线 -> 计算多模型残差 -> 赢家通吃”的逻辑进行反向推演。
4. **`src.utils`** 负责将结果进行可视化渲染。

## 4. 可扩展性 (Extensibility)
如果需要新增“变道 (Lane Changing)”场景：
- 在 `src/scenarios/` 下新增 `lane_changing.py`，定义切入切出模型。
- 在 `src/identification/` 下新增 `lane_changing_id.py`，定义基于侧向加速度或换道时距的辨识器。
- 在 `scripts/` 中复用或新增对应的 Pipeline 脚本。
