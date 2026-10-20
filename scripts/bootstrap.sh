#!/usr/bin/env bash
# 在新机器上从零恢复可运行环境。
#
# 前提：已 clone 本仓库，机器上装有 Homebrew 与 Xcode Command Line Tools。
# 用法：bash scripts/bootstrap.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
QLIB_TAG="v0.9.8"
QLIB_REPO="https://github.com/microsoft/qlib.git"

fail() { echo "[FAIL] $*" >&2; exit 1; }
ok()   { echo "[ OK ] $*"; }

cd "$ROOT" || fail "无法进入仓库根目录"
unset PYTHONPATH

echo "== 1. 系统依赖 =="
command -v brew >/dev/null 2>&1 || fail "未安装 Homebrew"
brew list libomp >/dev/null 2>&1 || { echo "安装 libomp..."; brew install libomp; }
brew list python@3.11 >/dev/null 2>&1 || { echo "安装 python@3.11..."; brew install python@3.11; }
ok "系统依赖就绪"

echo "== 2. qlib 源码 =="
if [ ! -d "$ROOT/vendor/qlib/qlib" ]; then
    mkdir -p "$ROOT/vendor"
    git clone --depth 1 --branch "$QLIB_TAG" "$QLIB_REPO" "$ROOT/vendor/qlib" || fail "克隆 qlib 失败"
fi
ok "vendor/qlib 就绪（$QLIB_TAG）"

echo "== 3. 虚拟环境 =="
if [ ! -x "$PY" ]; then
    /opt/homebrew/opt/python@3.11/bin/python3.11 -m venv "$ROOT/.venv" || fail "创建 venv 失败"
fi
ok "Python 3.11 虚拟环境就绪"

echo "== 4. 依赖 =="
"$PY" -m pip install -q --upgrade pip setuptools wheel || fail "升级 pip 失败"
"$PY" -m pip install -q -r "$ROOT/requirements.lock.txt" || fail "安装依赖失败"
ok "依赖安装完成"

echo "== 5. qlib editable 安装 =="
"$PY" -m pip install -q --no-deps --no-build-isolation -e "$ROOT/vendor/qlib" || fail "editable 安装失败"
ok "qlib 已链接到 vendor/qlib"

echo "== 6. 目录结构 =="
mkdir -p "$ROOT/data/raw" "$ROOT/data/qlib_cn" "$ROOT/reports"
ok "工作目录就绪"

echo "== 7. 示例数据 =="
if [ ! -d "$HOME/.qlib/qlib_data/cn_data/calendars" ]; then
    echo "下载 A 股示例数据（约 200MB）..."
    "$PY" "$ROOT/vendor/qlib/scripts/get_data.py" qlib_data \
        --target_dir "$HOME/.qlib/qlib_data/cn_data" --region cn || fail "数据下载失败"
fi
ok "数据就绪"

echo
echo "全部完成。验证："
echo "  bash $ROOT/scripts/reproduce_baseline.sh"
