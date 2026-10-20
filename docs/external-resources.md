# 外部资源清单：值得看的 qlib 仓库

> 收录时间：2026-10-20。所有仓库均已用 `git ls-remote` 验证存在。
> Star / 提交数为抓取时的页面值，仅供参考。
>
> **使用纪律（重要）**：这些仓库是**别人的实现**，不是你的资产。
> 读 README 和架构文档，对照自己的失败清单，**读完就关掉，不要 clone 下来跑**。
> 同时跑两套框架，会让你的实验环境立刻分裂。

---

## 一、按需求选，不要按 star 选

| 你想解决的问题 | 看这个 |
|---|---|
| qlib 怎么用，各模块干什么 | 先跑本仓库的 `scripts/walkthrough.py`，再看 `QuantWorld2022/qlib_tutorial` |
| 怎么接自己的数据（TuShare/聚宽） | `freenowill/qlib-zh` 的 `tushare/` 管道 |
| 怎么让结论可审计、可复现 | **`magic-alt/qlib-platform`**（最值得读） |
| 多模型怎么统一调度 | `CAPCHER0110/qlibbestpractice` |
| 自动因子挖掘怎么接 | `freenowill/qlib-zh` 的 `/factor-mining` 部分 |
| 完整回测报告怎么写 | `Damon0796/Qlib-` |
| 想要 Web 界面 | `cn-vhql/qlib_factor_platform` |

---

## 二、清单总览

| 仓库 | Star | 提交 | 定位 | 优先级 |
|---|---|---|---|---|
| `QuantWorld2022/qlib_tutorial` | 211 | 8 | 中文入门教程 | ⭐⭐⭐ |
| `magic-alt/qlib-platform` | 2 | **980** | 可审计 Alpha 工厂 | ⭐⭐⭐ |
| `freenowill/qlib-zh` | 8 | 57 | 实盘 + RD-Agent | ⭐⭐ |
| `CAPCHER0110/qlibbestpractice` | 1 | 7 | 多模型调度 | ⭐⭐ |
| `Damon0796/Qlib-` | — | — | 线性模型选股 | ⭐ |
| `cn-vhql/qlib_factor_platform` | — | — | Streamlit 界面 | ⭐ |
| `LinChengHao3606307/QuantitativeDeepLearningAnalystIntern` | — | — | 因子挖掘 + MLflow | ⭐ |
| `Daryl9441/hands-on-qlib` | 10 | 1 | 中文课程 10 课 | ⭐ |

**观察**：qlib 本体 49.5K star，第三方生态最高只有 211 star。这说明它"工程强、社区弱"，绝大多数是个人项目。

**star 与价值不相关**：`magic-alt/qlib-platform` 只有 2 star，但 980 次提交，方法论最严谨。

---

## 三、逐个说明

### 1. `QuantWorld2022/qlib_tutorial` ⭐⭐⭐

```
https://github.com/QuantWorld2022/qlib_tutorial
```

| 项 | 内容 |
|---|---|
| Star / Fork | 211 / 65 |
| 提交 | 8 |
| 许可 | MIT |
| 来源 | 公众号「量化投资与机器学习」(QIML) 配套 |

**内容**：按「数据篇 → 模型篇 → 策略篇」组织，两个 notebook + 一个策略目录，每段代码有中文解读。

**能学到**：
- qlib 的基本用法（虽然部分 API 已过时，见下方警告）
- 数据篇讲清楚 `D.features` 和表达式引擎
- 策略篇讲清楚从信号到持仓

**看哪几个文件**：
- `qlib数据篇.ipynb`
- `qlib模型篇.ipynb`
- `qlib策略篇/`

**警告**：这是 2021 年左右的教程，API 与 qlib 0.9.8 有出入。已知不一致：

| 教程写法 | 0.9.8 正确写法 |
|---|---|
| `ds.prepare()` | `ds.prepare("train")` |
| `pip install pyqlib` 直接用 | 需处理 mlflow 版本冲突 |

**结论**：当"概念图"看，不当"可执行代码"看。真正的可执行版本在本仓库 `scripts/walkthrough.py`。

---

### 2. `magic-alt/qlib-platform` ⭐⭐⭐ 最值得读

```
https://github.com/magic-alt/qlib-platform
```

| 项 | 内容 |
|---|---|
| Star / Fork | 2 / 1 |
| 提交 | **980** |
| 许可 | Apache-2.0 |
| 定位 | Auditable A-share Quant Research & Alpha Factory on Microsoft Qlib |

**它做的事，恰好覆盖了我们讨论过的全部方法论**：

| 关注点 | 它的实现 |
|---|---|
| 可复现 | 不可变 `DataRelease`、`DatasetVersion` 身份与血缘 |
| walk-forward | 设计原则第一条 "Walk-forward first"，支持固定 OOS / 滚动 OOS |
| PIT | `alpha158_pit_v1`、PIT 基本面、PIT 行业 |
| 多模型对比 | `matrix` 命令，Ridge / LGBM / XGB 同数据同协议对比 |
| 可审计 | 预测、模拟成交、策略决策可回放 |

它明确声明：**"不是 Qlib 的 fork 或替代品，而是使用并扩展 Qlib"**——定位和我们完全一致。

**能学到**：
- "可审计"如何变成具体的数据结构（不是口号）
- 研究矩阵怎么让模型对比变得公平
- AlphaPack 阶梯式设计（`alpha158_market_v1` → `alpha158_daily_v1` → `alpha158_pit_v1` → `multifactor_core_v1`）

**看哪几个文件**：
- `README.md` 的六条设计原则
- `docs/identity_and_lineage`（数据身份与血缘）
- `docs/architecture`
- `configs/pipeline.*.yaml`（看它怎么组织运行 profile）

**注意**：只有 2 star，刚开源，未经社区检验。980 次提交 / 2 star 的组合通常是"私有开发很久后一次性公开"。**读理念，不抄代码。**

---

### 3. `freenowill/qlib-zh` ⭐⭐

```
https://github.com/freenowill/qlib-zh
```

| 项 | 内容 |
|---|---|
| Star | 8 |
| 提交 | 57 |
| 许可 | MIT |
| 定位 | Qlib + RD-Agent，A 股实盘操作 |

**内容**：TuShare 数据管道（API 拉取 → 健康检查 → 因子注册 → H5 特征）、多市场 walk-forward LightGBM、Claude Code 斜杠命令、Docker 部署。

**能学到**：
- **数据管道怎么组织**（你接聚宽数据时最需要参考的部分）
- 健康检查环节的设计（对应我们的 `constraints/data_checks.py`）
- 自定义因子怎么和 Alpha158 拼在一起

**看哪几个文件**：
- `tushare/get_tushare_data.py`（数据拉取）
- `tushare/check_health.py`（健康检查，重点看）
- `CLAUDE.md`（架构说明，比 README 详细）

**注意**：8 star 的个人项目，代码质量未经检验。**抄结构，不抄实现。**

---

### 4. `CAPCHER0110/qlibbestpractice` ⭐⭐

```
https://github.com/CAPCHER0110/qlibbestpractice
```

| 项 | 内容 |
|---|---|
| Star | 1 |
| 提交 | 7 |
| 许可 | MIT |
| 定位 | 生产级量化平台，策略模式架构 |

**内容**：统一入口 `main.py` 通过 `MODEL_DISPATCHER` 分发到 TRA / LightGBM / LSTM / ALSTM / Transformer，训练与每日推理解耦，LightGBM 支持滚动重训，结果推 Redis。

**能学到**：
- 多模型如何用一份配置 + 一个注册表管理
- 滚动训练的参数设计：
  ```yaml
  rolling:
      enable: True
      step: 20           # 每隔 20 个交易日重训
      train_window: 242  # 每次回看一年
  ```

**看哪几个文件**：
- `main.py` 的 `MODEL_DISPATCHER`
- `config/lgbm_config.yaml`（滚动训练配置）
- `models/run_lgbm.py`

**注意**：7 次提交、无回测业绩，工程骨架可参考，结论不可信。

---

### 5. 其余（按需查）

| 仓库 | 用途 | 看什么 |
|---|---|---|
| `Damon0796/Qlib-` | 线性模型选股，含完整回测报告 | README 里的回测指标表写法 |
| `cn-vhql/qlib_factor_platform` | Streamlit 因子研究界面 | 如果想要可视化，看 `ui/` 和 `factors/` |
| `LinChengHao3606307/QuantitativeDeepLearningAnalystIntern` | 因子挖掘 + MLflow 追踪 | `Makefile` 和一键复现设计 |
| `Daryl9441/hands-on-qlib` | 中文课程 10 课 + 5 个 Lab | 适合结构化学习，但只有 1 次提交 |
| `xl0418/qlib-docs-cn` | 中文文档 28 章 | 查文档用，注意可能是 AI 生成，需核对 |

---

## 四、判断一个 qlib 项目值不值得看：五条标准

比清单更有用。以后看到任何 qlib 仓库，用这五条筛：

| # | 标准 | 不合格 | 合格 |
|---|---|---|---|
| 1 | 样本外 | "回测 2017-2020 年化 18%" | 明确切出训练/验证/样本外三段，说明样本外碰了几次 |
| 2 | PIT | 直接用财报 `statDate` | 用公告日，或明确声明"本项目无基本面因子" |
| 3 | 成本 | 不谈成本，或只算佣金 | 含印花税、滑点、冲击，单列"含成本/不含成本" |
| 4 | 数据溯源 | "下载数据即可" | 说清数据来源、快照日期、复权方式 |
| 5 | 提交历史 | 7 次提交，一次性上传 | 几十上百次迭代，能看到演进 |

按这五条筛，上面清单里**大部分会掉队**，包括那个 211 star 的教程——它是好教程，但不是好范本。

---

## 五、正确的使用方式

这些仓库真正的价值不在代码，在**别人的踩坑总结**。

用它们做三件事：

1. **对照失败清单**
   看到别人写"我们需要 PIT"，问自己：我的失败清单里有这条吗？
   看到别人写"walk-forward first"，问自己：我的 journal 记过这个教训吗？

2. **抄结构，不抄实现**
   比如 `freenowill/qlib-zh` 的健康检查环节，值得借鉴思路；但它的具体代码要自己重写，因为要接你自己的数据。

3. **验证自己的判断**
   如果你读完 `magic-alt/qlib-platform` 觉得"它做的和我想的一样"，说明你的方法论方向是对的，可以继续。
   如果觉得"我从没想过这个问题"，那就是你 journal 里缺的一块。

---

## 六、不要做的事

| 不要 | 原因 |
|---|---|
| clone 下来跑 | 同时跑两套框架，环境立刻分裂，基准失效 |
| 把别人的策略接到自己基准上对比 | 数据、成本、切分全不同，比出来的东西没有意义 |
| 因为某个仓库 star 高就信它的结论 | star 数衡量的是"传播度"，不是"正确性" |
| 收藏一堆仓库以为在积累 | 收藏动作本身不产生任何资产，journal 才产生 |

---

## 七、一句话总结

> **这些仓库能教你怎么写代码，教不了你怎么判断一个结论是否可信。**
> 后者只能靠你自己的 journal 和失败清单，一页一页攒出来。
