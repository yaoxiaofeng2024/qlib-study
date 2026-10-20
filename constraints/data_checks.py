"""数据质量强制校验。

设计原则：任何一条不通过，直接抛异常，拒绝进入训练与回测。
这些断言是「踩过的坑」的物化，每发现一次新问题，就在这里加一条。
"""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume", "factor"]

# 单只股票最少交易日数，少于该值不进入股票池
MIN_TRADING_DAYS = 250


class DataCheckError(AssertionError):
    """数据校验失败。不允许 catch 后继续跑。"""


def _fail(msg: str) -> None:
    raise DataCheckError(msg)


def check_schema(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        _fail(f"缺少必需列: {missing}，实际列: {list(df.columns)}")
    na_cols = [c for c in REQUIRED_COLUMNS if df[c].isna().any()]
    if na_cols:
        _fail(f"以下列存在空值: {na_cols}，空值行数: {df[na_cols].isna().sum().to_dict()}")


def check_ohlc(df: pd.DataFrame) -> None:
    bad_high = df["high"] < df[["open", "close", "low"]].max(axis=1) - 1e-8
    if bad_high.any():
        rows = df.loc[bad_high, ["date", "symbol"]].head(5).to_dict("records")
        _fail(f"high 小于 open/close/low 的行数={int(bad_high.sum())}，样例={rows}")

    bad_low = df["low"] > df[["open", "close", "high"]].min(axis=1) + 1e-8
    if bad_low.any():
        rows = df.loc[bad_low, ["date", "symbol"]].head(5).to_dict("records")
        _fail(f"low 大于 open/close/high 的行数={int(bad_low.sum())}，样例={rows}")

    nonpos = (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
    if nonpos.any():
        rows = df.loc[nonpos, ["date", "symbol"]].head(5).to_dict("records")
        _fail(f"价格非正的行数={int(nonpos.sum())}，样例={rows}")


def check_volume(df: pd.DataFrame) -> None:
    neg = df["volume"] < 0
    if neg.any():
        _fail(f"成交量为负的行数={int(neg.sum())}")


def check_duplicates(df: pd.DataFrame) -> None:
    dup = df.duplicated(subset=["date", "symbol"])
    if dup.any():
        sample = df.loc[dup, ["date", "symbol"]].head(5).to_dict("records")
        _fail(f"date+symbol 重复行数={int(dup.sum())}，样例={sample}")


def check_factor(df: pd.DataFrame) -> None:
    """复权因子必须为正，且单日变动不应剧烈跳变（跳变意味着数据源拼接错误）。"""
    if (df["factor"] <= 0).any():
        _fail("复权因子存在非正值")

    s = df.sort_values(["symbol", "date"])
    ratio = s.groupby("symbol")["factor"].shift(-1) / s["factor"]
    ratio = ratio.dropna()
    jump = (ratio > 1.5) | (ratio < 1 / 1.5)
    if jump.any():
        _fail(f"复权因子单日跳变超过 50% 的次数={int(jump.sum())}，请检查除权数据是否衔接")


def check_coverage(df: pd.DataFrame, min_days: int = MIN_TRADING_DAYS) -> None:
    counts = df.groupby("symbol")["date"].nunique()
    short = counts[counts < min_days]
    if len(short) > 0:
        _fail(
            f"{len(short)} 只股票交易日数少于 {min_days}，"
            f"样例={short.head(5).to_dict()}。请在股票池构建阶段显式剔除，不要静默保留。"
        )


def check_date_continuity(df: pd.DataFrame, calendar: list) -> None:
    """每只股票的日期必须落在交易日历内，且不能出现未来日期。"""
    cal = set(pd.to_datetime(calendar))
    dates = set(pd.to_datetime(df["date"].unique()))
    extra = dates - cal
    if extra:
        _fail(f"{len(extra)} 个日期不在交易日历内，样例={sorted(extra)[:5]}")


def run_all(df: pd.DataFrame, calendar: list | None = None) -> pd.DataFrame:
    """全部校验通过才返回，返回按 symbol, date 排序后的数据。"""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    check_schema(df)
    check_duplicates(df)
    check_ohlc(df)
    check_volume(df)
    check_factor(df)
    if calendar is not None:
        check_date_continuity(df, calendar)
    return df.sort_values(["symbol", "date"]).reset_index(drop=True)
