# 开发者与用户指南

## 1. 代码调试与配置修改

### 调整仿真参数
如果你希望模拟更快的车速或更近的跟车距离，可以修改 `src/scenarios/car_following.py` 中的 `generate_scenario_configs` 函数：

```python
speeds = [15.0, 25.0, 35.0]  # 修改这里的初始速度
thw_inits = [1.2, 1.8, 2.8]  # 修改初始时距
```

### 修改车辆动力学物理限制
打开 `src/core/vehicle.py`，可以修改车辆的底盘能力：
- `a_max`, `a_min`：最大加减速度限制。
- `tau`：一阶惯性滞后系数，值越大，车辆响应越迟钝。
- `jerk_max`：舒适度限制，决定了加速度变化的快缓。

## 2. 运行 Pipeline

项目采用典型的三段式数据流：

1. **仿真阶段** `python scripts/01_run_simulation.py`
   - **输入**: 场景配置参数矩阵。
   - **输出**: `output/data/simulation_dataset.csv` (约包含十几万行时序数据)。

2. **辨识阶段** `python scripts/02_run_identification.py`
   - **输入**: `simulation_dataset.csv`
   - **逻辑**: 执行滑动窗口切分、残差计算与胜者投票。
   - **输出**: `output/data/identification_results.csv`

3. **可视化阶段** `python scripts/03_run_visualization.py`
   - **输入**: 仿真与辨识的融合结果。
   - **输出**: 在 `output/figures/` 目录下生成一系列包含高质量 Seaborn 样式的分析图表，如 `confusion_matrix.png`, `scenario_performance.png` 等。

## 3. 常见问题 (FAQ)

- **Q: 为什么急刹场景的辨识准确率较低？**
  - A: 在极限工况下，动作受限于物理限幅（如 $-5m/s^2$）。算法在 `identification` 层提供了 `valid_ratio` 字段，你可以利用该字段过滤掉这些异常工况的数据。
