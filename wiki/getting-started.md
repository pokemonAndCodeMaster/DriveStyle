# 快速开始与使用手册

本指南涵盖了 DriveStyle 的核心工作流，包括测试用例生成、单用例高保真分析以及大规模用例集的批量回归验证。

## 🛠️ 环境配置

DriveStyle 要求 Python 3.10+ 环境及常用的数据科学库。

```bash
# 克隆仓库
git clone https://github.com/your-repo/DriveStyle.git
cd DriveStyle

# 安装依赖
pip install -r requirements.txt
```

## 🧪 工作流 1: 生成模拟测试数据

系统提供了一个便捷的脚本来生成包含 Ground Truth 的测试用例（支持 JSON 和 CSV 格式）。

```bash
# 生成一个目标 THW 为 1.2s 的激进型测试用例
python3 scripts/generate_test_case.py --thw 1.2 --out_json tests/data/case_aggressive.json
```

- **输出**: 自动生成 `tests/data/case_aggressive.json` 和 `tests/data/case_aggressive.csv`。

## 🔍 工作流 2: 单用例高保真分析

使用 `run_single_case.py` 对特定片段进行深度解剖。这会生成一张 **“五面合一超融合图”**，融合了：
-   **物理动态**: 自车/前车速度、加速度、相对距离。
-   **观测时距**: 实时计算的 THW 观测值。
-   **算法中间态**: 所有风格假设 (1.0s, 1.5s, 2.0s) 的残差演化路径。
-   **决策阶梯**: 最终判定的风格输出。

```bash
# 分析一个 debug.json 文件
python3 scripts/run_single_case.py --file debug.json
```

- **可视化产物**: `output/figures/debug_result_segment_X_dynamics.png`。

## 📊 工作流 3: 批量验证与全量报表

为了验证算法在多工况下的整体表现，请使用 `run_batch_cases.py`。该脚本会遍历目录下的所有用例，并输出统计结果。

```bash
# 处理 tests/data 目录下所有用例，并设置最多绘制 5 张分析图
python3 scripts/run_batch_cases.py --dir tests/data --plot_limit 5 --out output/data/batch_report.csv
```

### 📈 自动生成的统计图表
批量脚本会在 `output/figures/` 下自动生成：
- **混淆矩阵 (Confusion Matrix)**: 直观展示风格识别的准确率与误判分布。
- **风格分布箱线图 (Style Distribution)**: 展示辨识结果的离散度与偏差。
- **工况性能对比图 (Scenario Performance)**: 按工况类型（如匀速、制动等）统计识别成功率。

### 📋 增强型结果表格
汇总报表 `batch_report.csv` 包含了详尽的片段级元数据：
- `segment_id`, `target_id`, `total_duration` (片段 ID、目标 ID、持续时长)
- `identified_style` vs `gt_style` (辨识值与真实值对比)
- `cost_1.0`, `cost_1.5`, `cost_2.0` (各假设下的残差值)
- `avg_v_ego`, `avg_dist` (平均速度、平均间距等上下文指标)

---

*由 [Mini-Wiki v3.0.6](https://github.com/trsoliu/mini-wiki) 自动生成 | 2026-03-14*
