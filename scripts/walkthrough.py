#!/usr/bin/env python
"""qlib 模块巡游：每一层的最小可跑示例。

目的：跑完这 8 个 stage，你就知道 qlib 是由哪几块拼起来的，以及
      journal 里那条流水线（数据→特征→标签→模型→信号→回测）在代码里长什么样。

用法：
    .venv/bin/python scripts/walkthrough.py data
    .venv/bin/python scripts/walkthrough.py all

每个 stage 都可以单独跑，互不依赖（除了 model 会重算一次特征）。
"""

from __future__ import annotations

import argparse
import time

import qlib
from qlib.data import D

PROVIDER = "~/.qlib/qlib_data/cn_data"

# 用小窗口，保证每个 stage 都在一分钟内跑完
FIT_START, FIT_END = "2015-01-01", "2015-12-31"
TRAIN = ("2015-01-01", "2015-12-31")
VALID = ("2016-01-01", "2016-06-30")
TEST = ("2016-07-01", "2016-12-31")

_segments = {"train": TRAIN, "valid": VALID, "test": TEST}


def init():
    qlib.init(provider_uri=PROVIDER, region="cn")


def banner(n: str, title: str, purpose: str):
    print("\n" + "=" * 72)
    print(f"  [{n}] {title}")
    print(f"  解决什么问题：{purpose}")
    print("=" * 72)


# --------------------------------------------------------------------------
def stage_data():
    """模块 1：数据层 D —— 交易日历 / 股票池 / 取数"""
    banner("1", "数据层 qlib.data.D", "统一入口读取 bin 数据，屏蔽文件结构")

    cal = D.calendar(start_time="2020-08-24", end_time="2020-09-04")
    print(f"\nD.calendar 交易日历：{len(cal)} 天，{cal[0].date()} ~ {cal[-1].date()}")

    codes = D.list_instruments(
        D.instruments("csi300"), start_time="2020-09-01", end_time="2020-09-04", as_list=True
    )
    print(f"D.instruments('csi300') 成分数：{len(codes)}，前 5 个：{codes[:5]}")

    df = D.features(["SH600000"], ["$close", "$volume"], start_time="2020-09-01", end_time="2020-09-04")
    print("\nD.features 单字段取数（索引是 instrument + datetime，二维）：")
    print(df.to_string())

    print("\n>> 要点：返回值永远是 (instrument, datetime) 二维索引。")
    print(">> 你自己写代码时 80% 的隐蔽 bug（shift 错位、跨股票串行）都来自破坏了这个结构。")


# --------------------------------------------------------------------------
def stage_expression():
    """模块 2：表达式引擎 —— 用一行公式写因子"""
    banner("2", "表达式引擎 qlib.data.ops", "因子不用写循环，一行公式对全市场全历史生效")

    exprs = {
        "$close": "收盘价",
        "Ref($close, 1)": "昨收（严格滞后 1 期）",
        "Mean($close, 5)": "5 日均线",
        "Std($close, 20)": "20 日波动",
        "($close-Ref($close,1))/Ref($close,1)": "日收益率",
        "Corr($close, $volume, 10)": "量价 10 日相关性",
    }

    for expr, note in exprs.items():
        df = D.features(["SH600000"], [expr], start_time="2020-09-01", end_time="2020-09-04")
        vals = ", ".join(f"{v:.4f}" for v in df.iloc[:, 0].values)
        print(f"  {expr:38s} {note:18s} {vals}")

    print("\n>> 要点：Ref 自带滞后语义，写不出零滞后版本。手写 df.shift(1) 很容易漏，且不报错。")
    print(">> 你以后加自定义因子，就是往 configs 里加一行表达式，不是加一个 py 文件。")


# --------------------------------------------------------------------------
def _build_handler():
    from qlib.contrib.data.handler import Alpha158

    return Alpha158(
        instruments="csi300",
        start_time=TRAIN[0],
        end_time=TEST[1],
        fit_start_time=FIT_START,
        fit_end_time=FIT_END,  # 关键：标准化统计量只用到训练期末
    )


def stage_handler():
    """模块 3：Handler —— 特征 + 标签 + 预处理"""
    banner("3", "Handler Alpha158", "把原始价量变成模型能吃的特征矩阵和标签")

    t0 = time.time()
    h = _build_handler()
    feat = h.fetch(col_set="feature")
    label = h.fetch(col_set="label")

    print(f"\n特征矩阵 shape = {feat.shape}   （行=股票×日期，列=158 个因子）")
    print(f"标签向量 shape = {label.shape}")
    print(f"\n特征列前 8 个：{list(feat.columns[:8])}")
    print(f"标签列：{list(label.columns)}")
    print(f"\n特征样例（前 3 行 × 5 列）：")
    print(feat.iloc[:3, :5].to_string())
    print(f"\n标签样例：")
    print(label.head(3).to_string())
    print(f"\n耗时 {time.time() - t0:.1f}s")

    print("\n>> 要点：Alpha158 的标签是 Ref($close,-2)/Ref($close,-1)-1，")
    print(">>      即 T+1 开盘附近买入、T+2 收盘平仓，符合 A 股 T+1。")
    print(">> 要点：fit_start_time/fit_end_time 只覆盖训练期，这是防泄漏的关键一行。")


def stage_dataset():
    """模块 4：Dataset —— 按时间切分"""
    banner("4", "Dataset DatasetH", "把一份数据切成 train / valid / test，严格按时间")

    h = _build_handler()
    from qlib.data.dataset import DatasetH

    ds = DatasetH(handler=h, segments=_segments)

    # 注意：qlib 0.9.8 的 prepare() 必须传 segment 名字，不能空参。
    # 网上大量旧教程写 ds.prepare()，在 0.9.8 上直接 TypeError。
    for name in ["train", "valid", "test"]:
        d = ds.prepare(name)
        idx = d.index.get_level_values("datetime")
        print(f"  {name:6s} shape={d.shape}  日期 {idx.min().date()} ~ {idx.max().date()}")

    print("\n>> 要点：切分是硬切，没有随机打乱。随机 K-Fold 在时序上必然泄漏。")
    print(">> 这份切分就是 yaml 里 segments 那一段，没有任何魔法。")


def stage_model():
    """模块 5：模型 —— 训练与预测"""
    banner("5", "模型 LGBModel", "把特征矩阵映射成预期收益打分")

    from qlib.contrib.model.gbdt import LGBModel
    from qlib.data.dataset import DatasetH

    h = _build_handler()
    ds = DatasetH(handler=h, segments=_segments)

    model = LGBModel(
        loss="mse",
        learning_rate=0.1,
        num_leaves=64,
        max_depth=6,
        num_threads=4,
        early_stopping_rounds=20,
    )

    t0 = time.time()
    model.fit(ds)
    print(f"\n训练完成，耗时 {time.time() - t0:.1f}s")

    pred = model.predict(ds, segment="test")
    print(f"预测结果 shape = {pred.shape}（test 段每只股票每天一个分数）")
    print(pred.head(5).to_string())

    print("\n>> 要点：模型只做一件事——打分。它不知道成本、不知道涨跌停、不知道组合。")
    print(">> 换模型（XGB/线性/LSTM）只改这一块，上下游完全不动。")


def stage_signal():
    """模块 6：Record —— 存预测、算 IC"""
    banner("6", "实验记录 SignalRecord / SigAnaRecord", "把预测和评估结果存进 mlflow，可追溯")

    from qlib.contrib.model.gbdt import LGBModel
    from qlib.data.dataset import DatasetH
    from qlib.workflow import R
    from qlib.workflow.record_temp import SigAnaRecord, SignalRecord

    import mlflow

    h = _build_handler()
    ds = DatasetH(handler=h, segments=_segments)
    model = LGBModel(loss="mse", learning_rate=0.1, num_leaves=64, num_threads=4, verbose_eval=-1)
    model.fit(ds)

    # 前面若有残留的 active run，R.start 会直接抛异常
    mlflow.end_run()

    with R.start(experiment_name="walkthrough"):
        R.save_objects(model=model)
        rec = R.get_recorder()

        sr = SignalRecord(model, ds, rec)
        sr.generate()
        pred = sr.load("pred.pkl")
        print(f"\nSignalRecord 存下预测：shape={pred.shape}")

        sar = SigAnaRecord(rec)
        sar.generate()
        ic = sar.load("ic.pkl")
        ric = sar.load("ric.pkl")
        print(f"IC    均值={ic.mean():.4f}  ICIR={ic.mean() / ic.std():.2f}")
        print(f"RankIC 均值={ric.mean():.4f}  RankICIR={ric.mean() / ric.std():.2f}")
        print(f"\n产物目录：{rec.get_local_dir()}")

    print("\n>> 要点：这一块就是『积累』的载体。每次实验的预测、IC、模型全都落盘。")
    print(">> 没有这一步，你三个月后无法回答『上次那个结论是怎么来的』。")


def stage_backtest():
    """模块 7：回测 —— 信号变成持仓，持仓变成收益"""
    banner("7", "回测 PortAnaRecord", "把打分变成持仓，再算上成本和涨跌停")

    from qlib.contrib.model.gbdt import LGBModel
    from qlib.data.dataset import DatasetH
    from qlib.workflow import R
    from qlib.workflow.record_temp import PortAnaRecord, SignalRecord

    import mlflow

    h = _build_handler()
    ds = DatasetH(handler=h, segments=_segments)
    model = LGBModel(loss="mse", learning_rate=0.1, num_leaves=64, num_threads=4, verbose_eval=-1)
    model.fit(ds)

    mlflow.end_run()

    cfg = {
        "strategy": {
            "class": "TopkDropoutStrategy",
            "module_path": "qlib.contrib.strategy.signal_strategy",
            "kwargs": {"signal": "<PRED>", "topk": 20, "n_drop": 2},
        },
        "backtest": {
            "start_time": TEST[0],
            "end_time": TEST[1],
            "account": 100_000_000,
            "benchmark": "SH000300",
            "exchange_kwargs": {
                "limit_threshold": 0.095,
                "deal_price": "close",
                "open_cost": 0.0005,
                "close_cost": 0.0015,
                "min_cost": 5,
            },
        },
    }

    with R.start(experiment_name="walkthrough_bt"):
        rec = R.get_recorder()
        SignalRecord(model, ds, rec).generate()
        PortAnaRecord(rec, cfg, risk_analysis_freq="day").generate()
        # port_analysis_1day.pkl 的索引是 (收益类型, 指标)，
        # 收益类型形如 excess_return_with_cost / excess_return_without_cost
        report = rec.load_object("portfolio_analysis/port_analysis_1day.pkl")
        print("\n回测结果（含成本）：")
        print(report.loc["excess_return_with_cost"].to_string())

    print("\n>> 要点：strategy 决定买哪些、买多少；exchange 决定能不能成交、扣多少钱。")
    print(">> 你在 baseline 里看到的 8.07%，就是这两块的乘积。")


def stage_workflow():
    """模块 8：Workflow —— yaml 把上面全部串起来"""
    banner("8", "工作流 qrun", "一个 yaml 声明整条链路，qrun 执行")

    print("""
yaml 里的每一块，对应你刚跑过的一个 stage：

  qlib_init              →  stage 1  数据层
  task.dataset.handler   →  stage 3  Handler（Alpha158）
  task.dataset.segments  →  stage 4  时间切分
  task.model             →  stage 5  模型
  record.SignalRecord    →  stage 6  存预测
  record.SigAnaRecord    →  stage 6  算 IC
  record.PortAnaRecord   →  stage 7  回测
  port_analysis_config   →  stage 7  策略 + 交易所

执行：
  cd vendor/qlib/examples
  qrun benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml

>> 所以 qrun 不是黑盒，它就是按顺序实例化上面这些类。
>> 你改 yaml = 改实验，不用改代码。这就是能持续迭代的原因。
""")


STAGES = {
    "data": stage_data,
    "expression": stage_expression,
    "handler": stage_handler,
    "dataset": stage_dataset,
    "model": stage_model,
    "signal": stage_signal,
    "backtest": stage_backtest,
    "workflow": stage_workflow,
}


def main():
    parser = argparse.ArgumentParser(description="qlib 模块巡游")
    parser.add_argument("stage", choices=[*STAGES, "all"], help="要跑的模块")
    args = parser.parse_args()

    init()

    if args.stage == "all":
        for name, fn in STAGES.items():
            fn()
            print()
        print("\n全部完成。现在回头看 journal/00_baseline.md，每一行数字你都能指出它来自哪一块。")
    else:
        STAGES[args.stage]()


if __name__ == "__main__":
    main()
