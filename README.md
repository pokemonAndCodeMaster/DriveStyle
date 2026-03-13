# DriveStyle: Autonomous Driving Style Identification Engine

## 项目简介 (Overview)
**DriveStyle** 是一个面向自动驾驶与智能网联汽车的高保真“驾驶风格辨识”开源框架。本项目旨在通过建立严谨的物理与控制模型，从杂乱的时序跟车轨迹中，精准、可解释地解耦出人类驾驶员或自动驾驶系统的核心“意图特征”（如保守、普通、激进）。

本项目将复杂的风格辨识问题解构为：
1. **基础动力学还原**：考虑时延、限幅等物理约束。
2. **场景自动化生成**：支持各种极限工况（如急刹、随机扰动）的泛化生成。
3. **多宇宙假设检验**：基于“误差跟踪模型”（弹簧-跑步机理论）的白盒辨识算法。

目前已完整支持 **跟车场景 (Car Following)**，并具备极高的扩展性，可轻松拓展至变道、路口通行等其他场景。

## 快速开始 (Quick Start)

### 1. 环境准备
```bash
pip install -r requirements.txt
```

### 2. 运行 Pipeline
整个验证流程被拆分为三个标准化的阶段：

```bash
# 1. 运行仿真引擎，生成海量包含各种工况的跟车时序数据
python scripts/01_run_simulation.py

# 2. 运行辨识算法，基于多宇宙理论进行风格打标
python scripts/02_run_identification.py

# 3. 运行可视化报表，生成混淆矩阵与时序残差分析图
python scripts/03_run_visualization.py
```

## 文档导航 (Documentation)
详细的技术细节和架构说明请参考 `docs/` 目录：
- [整体架构设计 (Architecture)](docs/architecture.md)
- [跟车场景辨识原理 (Car Following Theory)](docs/scenario_following.md)
- [开发者与用户指南 (User Guide)](docs/user_guide.md)
