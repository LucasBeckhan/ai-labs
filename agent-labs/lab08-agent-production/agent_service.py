#!/usr/bin/env python3
"""
Lab 08 — Agent 生产化：把工具 Agent 变成 K8s 里的 HTTP 服务
===========================================================

【工程化三件事】（与 llmops-labs Lab06 的 RAG 服务同一套路，可对照学习）
  ① 进程化：FastAPI /run 接口（Agent 循环包进 HTTP）
  ② 可观测：/metrics 暴露请求数/耗时/工具调用数（Prometheus 注解发现）
  ③ 安全：接口层超时与步数限制（防止一次坏请求拖死服务）

【运行】
  本地冒烟：uvicorn agent_service:app --port 18002
  K8s：见 manifests/agent.yaml（构建镜像后 kind load + kubectl apply）
"""
import time

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

# 复用 Lab02 的注册表与 LLM 封装、Lab01 的循环模式
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab02-tool-registry"))
from registry_agent import registry, llm, parse_json  # noqa: E402

app = FastAPI()

# 进程内指标（与 llmops lab06 同款的最小可观测实现；多副本时由 Prometheus 按实例聚合）
REQS = 0
TOOL_CALLS = 0
LATENCY_MS = 0.0


def run_agent(task: str, max_steps: int = 5) -> dict:
    """Agent 主循环（Lab01 骨架 + 循环检测 + 降级出口），返回结构化轨迹便于排查。"""
    global TOOL_CALLS
    import json
    system = ("你是会使用工具的助手。工具清单：\n" + registry.manifest() + "\n"
              '需要工具时只输出 {"action": "工具名", "args": {...}}；'
              '能给答案时只输出 {"action": "final_answer", "answer": "..."}')
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    seen, trace = {}, []
    for step in range(1, max_steps + 1):
        d = parse_json(llm(messages))
        action = d.get("action")
        trace.append(d)
        if action == "final_answer":
            return {"answer": d.get("answer", ""), "steps": step, "trace": trace}
        if not action or action == "parse_error":
            messages += [{"role": "user", "content": "格式错误，只输出一行 JSON"}]
            continue
        if action in registry._tools:
            args = d.get("args", {}) if isinstance(d.get("args"), dict) else {}
            key = (action, str(sorted(args.items())))
            if key in seen:
                messages += [{"role": "user", "content": f"已调用过，结果 {seen[key]}，请给 final_answer。"}]
                continue
            result = registry.execute(action, args)
            seen[key] = result
            TOOL_CALLS += 1
            messages += [{"role": "user", "content": f"工具返回：{result}"}]
        else:
            messages += [{"role": "user", "content": f"工具不存在，可用：{list(registry._tools)}"}]
    return {"answer": "(未完成)", "steps": max_steps, "trace": trace}


@app.get("/run")
def run(task: str):
    """主接口：task 查询参数 → Agent 执行 → 答案 + 步数 + 轨迹。"""
    global REQS, LATENCY_MS
    t0 = time.time()
    out = run_agent(task)
    REQS += 1
    LATENCY_MS += (time.time() - t0) * 1000
    return out


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return (
        "# HELP agent_requests_total total agent runs\n# TYPE agent_requests_total counter\n"
        f"agent_requests_total {REQS}\n"
        "# HELP agent_tool_calls_total total tool invocations\n# TYPE agent_tool_calls_total counter\n"
        f"agent_tool_calls_total {TOOL_CALLS}\n"
        "# HELP agent_latency_ms_sum cumulative latency ms\n# TYPE agent_latency_ms_sum counter\n"
        f"agent_latency_ms_sum {LATENCY_MS:.0f}\n"
    )
