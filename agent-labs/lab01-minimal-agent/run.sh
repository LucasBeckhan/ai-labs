#!/bin/bash
# 固定使用项目已准备好的依赖环境，不依赖终端/PyCharm的默认Python。
set -euo pipefail
LAB_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$LAB_DIR/../.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/llmops-labs/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  echo "未找到项目虚拟环境：$PYTHON_BIN" >&2
  exit 1
fi
export LITELLM_LOCAL_MODEL_COST_MAP="${LITELLM_LOCAL_MODEL_COST_MAP:-True}"
exec "$PYTHON_BIN" -u "$LAB_DIR/minimal_agent.py" "$@"
