#!/usr/bin/env python3
"""
Lab 05 — 多 Agent 协作：Planner-Executor 模式
==============================================

【为什么需要多 Agent】
单个 Agent 上下文塞太多职责会互相干扰（提示词膨胀 + 注意力稀释）。
生产做法是"分工"：Planner 只做拆解（输出步骤清单），Executor 只做执行（每步一个专注的上下文）。
这是 LangGraph/AutoGen 里最常用的编排模式，也是"多 Agent 系统"的最小入门。

【本实验的协作协议】
  Planner（1 次）：任务 → JSON 步骤清单 [{"step": n, "description": "...", "tool_hint": "..."}]
  Executor（N 次）：逐步执行，每步拿到"总计划 + 当前步骤"，可调用工具，输出结果
  汇总（1 次）：全部结果 → 最终报告

【运行前提】网关 localhost:4000（复用 Lab02 的工具注册表）
【运行】../.venv/bin/python planner_executor.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab02-tool-registry"))
from registry_agent import registry, llm, parse_json  # noqa: E402  复用工具注册表与 LLM 封装


def plan(task: str) -> list[dict]:
    """Planner Agent：只负责把任务拆成 2-4 个可执行步骤（不执行任何工具）。

    给 Planner 的提示词刻意"窄"：只输出步骤清单。
    提示词窄 = 注意力集中 = 小模型也能稳定输出结构化计划。
    """
    raw = llm([
        {"role": "system", "content":
         "你是任务规划师。把用户任务拆解成 2-4 个步骤。"
         '只输出 JSON：{"steps": [{"step": 1, "description": "做什么", "tool_hint": "建议工具名"}]}'
         f"可用工具：{list(registry._tools)}"},
        {"role": "user", "content": task},
    ])
    d = parse_json(raw)
    steps = d.get("steps", [])
    print(f"\n📋 Planner 产出 {len(steps)} 个步骤:")
    for s in steps:
        print(f"   {s.get('step')}. {s.get('description')} (建议工具: {s.get('tool_hint')})")
    return steps


def execute_step(step: dict, task: str, tool_results: list[str]) -> str:
    """Executor Agent：执行单个步骤。

    每步的上下文 = 总任务 + 当前步骤 + 前面步骤的结果（协作的"共享黑板"）。
    Executor 内部是一个 mini 循环：调工具（最多 2 次）或直接给该步结论。
    """
    prior = "\n".join(f"步骤{i+1}结果: {r}" for i, r in enumerate(tool_results)) or "(无)"
    messages = [
        {"role": "system", "content":
         f"总任务: {task}\n已完成: {prior}\n你当前只负责执行这一步: {json.dumps(step, ensure_ascii=False)}\n"
         '需要工具时输出 {"action": "工具名", "args": {...}}；'
         '否则输出 {"action": "final_answer", "answer": "本步骤结论"}'},
    ]
    for _ in range(4):   # 每步最多 4 次交互（工具调用 + 参数修正重试 + 总结 + 容错）
        d = parse_json(llm(messages))
        action = d.get("action")
        if action == "final_answer" or not action:
            return str(d.get("answer", "(该步无输出)"))
        if action in registry._tools:
            args = d.get("args", {}) if isinstance(d.get("args"), dict) else {}
            result = registry.execute(action, args)
            print(f"   🔧 执行 {action}{args} → {str(result)[:60]}")
            # 参数错误时明确要求"修正后重试"；正常结果才让模型给结论
            if str(result).startswith("错误"):
                messages += [{"role": "user", "content": f"工具报错：{result}。请修正参数重新调用工具。"}]
            else:
                messages += [{"role": "user", "content": f"工具返回：{result}。请给出本步骤结论。"}]
        else:
            messages += [{"role": "user", "content": f"工具不存在，可用：{list(registry._tools)}"}]
    return "(该步超时未完成)"


def summarize(task: str, results: list[str]) -> str:
    """汇总 Agent：把各步结果合成最终报告（可复用 Executor 的上下文）。"""
    return llm([
        {"role": "system", "content": "根据各步骤结果，给用户一个简明最终答案（三句话以内）。"},
        {"role": "user", "content": f"任务: {task}\n各步结果: {json.dumps(results, ensure_ascii=False)}"},
    ])


def run(task: str):
    print(f"\n{'=' * 62}\n任务: {task}")
    steps = plan(task)
    if not steps:
        return "(Planner 未产出步骤——换 qwen-strong 重试)"
    results = []
    for s in steps:
        print(f" ▶ 执行步骤 {s.get('step')}: {s.get('description')}")
        results.append(execute_step(s, task, results))
    final = summarize(task, results)
    print(f"\n✅ 最终报告: {final}")
    return final


if __name__ == "__main__":
    run("先算 128 乘以 64，再统计句子'big data meets ai' 的英文单词数，最后把两个结果各用一句话总结")
