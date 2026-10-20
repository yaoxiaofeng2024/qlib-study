#!/usr/bin/env bash
# 运行官方测试套件，验证 qlib 框架本身完好。
#
# 之所以要复制到仓库外：vendor/qlib 在 sys.path 中会遮蔽已安装包，
# 导致 import qlib 命中未编译源码，报 No module named 'qlib.data._libs.rolling'。
#
# 之所以跑完要清理 Users/：qlib 测试代码用 lstrip("file:") 处理路径，
# 会剥离所有 f/i/l/e/: 字符，把 /Users/xxx 变成 Users/xxx，在 cwd 下建假目录。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
TESTS="$ROOT/_official_tests"

fail() { echo "[FAIL] $*" >&2; exit 1; }
ok()   { echo "[ OK ] $*"; }

cleanup() {
    rm -rf "$TESTS" "$ROOT/Users" "$ROOT/.pytest_cache"
}
trap cleanup EXIT

echo "== 准备测试目录 =="
rm -rf "$TESTS"
cp -r "$ROOT/vendor/qlib/tests" "$TESTS" || fail "复制测试目录失败"
rm -rf "$TESTS/rl"   # RL 测试仅支持 Linux 且需要额外依赖
ok "已复制到 $TESTS"

echo "== 运行端到端测试 =="
cd "$ROOT" || fail "无法进入仓库根目录"
unset PYTHONPATH
"$PY" -m pytest "$TESTS/test_all_pipeline.py" -q --tb=short
RET=$?

echo
if [ $RET -eq 0 ]; then
    ok "官方测试全部通过，框架完好"
else
    fail "官方测试未通过，先修环境再做实验"
fi
