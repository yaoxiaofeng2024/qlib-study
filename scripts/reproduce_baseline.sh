#!/usr/bin/env bash
# 复现 journal/00_baseline.md 中记录的冻结基准。
# 数据指纹不符时直接退出，避免在错误数据上得出错误结论。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
QRUN="$ROOT/.venv/bin/qrun"
DATA="$HOME/.qlib/qlib_data/cn_data"

EXPECT_CAL_MD5="197ff46b013e260eb82ed7f2b39ed297"
EXPECT_CSI300_MD5="337ab3bec3eab552fa8fb8db5a4f0fc1"

fail() { echo "[FAIL] $*" >&2; exit 1; }
ok()   { echo "[ OK ] $*"; }

echo "== 1. 环境 =="
[ -x "$PY" ] || fail "虚拟环境不存在：$PY"
# CodeBuddy/IDE 可能注入 PYTHONPATH 指向 shim，会干扰 pip 与 import
unset PYTHONPATH
"$PY" - <<'EOF' || exit 1
import qlib, lightgbm, mlflow, numpy, pandas
assert qlib.__version__ == "0.9.8", f"qlib 版本不符：{qlib.__version__}"
assert numpy.__version__ < "2", f"numpy 必须 <2，当前 {numpy.__version__}"
assert mlflow.__version__.startswith("2."), f"mlflow 必须 2.x，当前 {mlflow.__version__}"
print(f"qlib {qlib.__version__} | lgbm {lightgbm.__version__} | mlflow {mlflow.__version__} | numpy {numpy.__version__} | pandas {pandas.__version__}")
EOF
ok "依赖版本正确"

echo "== 2. 数据指纹 =="
[ -d "$DATA" ] || fail "数据目录不存在：$DATA，请先运行 vendor/qlib/scripts/get_data.py"
CAL_MD5="$(md5 -q "$DATA/calendars/day.txt")"
CSI300_MD5="$(md5 -q "$DATA/instruments/csi300.txt")"
[ "$CAL_MD5" = "$EXPECT_CAL_MD5" ] || fail "交易日历指纹不符：$CAL_MD5 != $EXPECT_CAL_MD5"
[ "$CSI300_MD5" = "$EXPECT_CSI300_MD5" ] || fail "csi300 股票池指纹不符：$CSI300_MD5 != $EXPECT_CSI300_MD5"
ok "交易日历与股票池指纹一致"

echo "== 3. 运行 baseline =="
cd "$ROOT/vendor/qlib/examples" || fail "examples 目录不存在"
"$QRUN" benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml 2>&1 | grep -A6 "excess return"

echo
echo "对照 journal/00_baseline.md：含成本年化应为 0.080654，IR 0.914486"
