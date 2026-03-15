# 快速上手与实验 SOP

本指南将带你走完 DriveStyle V14.0 的完整研判流程，从原始数据加载到生成终极量化报告。

## 📥 Step 1: 准备数据

将你的跟车数据片段命名为 `debug.json`。确保包含以下 Label：
- `23010101`: 自车速度与加速度。
- `17010900`: 前车 ID、间距、前车速度与加速度。

## ⚙️ Step 2: 调节配置

打开 `config/default_config.yaml`，根据实验需求修改参数：
```yaml
identification:
  targets:
    wn: [0.4, 0.8, 1.4]    # 对比三种响应带宽
    zeta: [0.7, 1.0, 1.5]  # 对比三种阻尼性格
```

## 🚀 Step 3: 运行研判流水线

执行以下脚本启动全自动化实验：
```bash
python3 scripts/run_param_sweep.py --file debug.json
```

### 该脚本将自动完成以下任务：
1.  **物理仿真扫参**：计算 27 组参数组合的拟合残差。
2.  **生成热力图**：输出参数敏感度地图。
3.  **渲染全景画布**：输出 6 份包含 10s 稳态射线的高清看板。
4.  **导出量化主表**：生成 `ultimate_master_report.csv`。

## 📊 Step 4: 结果研判

1.  **看精度**：查阅 `ultimate_master_report.csv` 中的 `MAE` 列，寻找拟合度最高的参数。
2.  **看收敛**：查阅 `ultimate_comp_Ws_Xs_wn_X.png`，观察 1.0s 射线是否精准指向 1.0 刻度。
3.  **看性格**：通过 `JerkVar` 指标评估该司机的脚法是否属于“躁动派”或“平顺派”。

---

*由 [Mini-Wiki v3.0.6](https://github.com/trsoliu/mini-wiki) 自动生成 | 2026-03-14*
