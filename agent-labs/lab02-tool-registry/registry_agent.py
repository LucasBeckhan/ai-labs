#!/usr/bin/env python3
"""
Lab 02 — 工具注册表与 JSON Schema：给 Agent 一套"正规的"工具体系
================================================================

【与 Lab 01 的差异】Lab 01 的工具注册表只有一个"描述"字符串；
真实系统（和 OpenAI function calling 规范）里，每个工具还带 **JSON Schema**——
参数的名字、类型、是否必填、取值范围的机器可读说明书。

本实验实现一个生产级工具注册表：
  ① 装饰器 @tool 一行代码注册（开发者体验）
  ② JSON Schema 自动生成（从 Python 类型注解提取）
  ③ 入参校验（模型传错类型/缺参数时，返回可读错误让模型重试而不是崩溃）
  ④ 工具执行隔离（单个工具异常不影响 Agent 主循环）

这也是 MCP（Lab 06）和 OpenAI tools API 的工具定义格式——学会这一层，
所有框架的工具系统你都看得懂。

【运行前提】LiteLLM 网关在 localhost:4000
【运行方式】../.venv/bin/python registry_agent.py "上海今天多少度？不对，我没有天气工具，请算 123*456"
"""
import inspect
import json
import os
import re
import sys

import litellm
from typing import Callable, get_type_hints

GATEWAY = os.environ.get("GATEWAY", "http://localhost:4000")
MODEL = os.environ.get("MODEL", "qwen-small")

# Python 类型注解 → JSON Schema 类型的映射表（覆盖常用类型即可）
PY_TO_JSON_SCHEMA = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}


# ---------------------------------------------------------------------------
# 注册表实现：装饰器 + Schema 自动生成
# ---------------------------------------------------------------------------

class ToolRegistry:
    """工具注册表：Agent 工具体系的"单一事实来源"。

    职责：注册（@tool）、生成给模型的工具说明书、执行时校验入参。
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def tool(self, description: str):
        """装饰器工厂：@registry.tool(description="...") 把普通函数注册成 Agent 工具。

        自动从函数的 docstring/类型注解/签名提取：
          - 参数名与类型 → JSON Schema 的 properties
          - 无默认值的参数 → required 列表
        """
        def decorator(fn: Callable):
            # --- 从签名和类型注解提取参数 schema ---
            sig = inspect.signature(fn)
            hints = get_type_hints(fn)
            properties, required = {}, []
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                py_type = hints.get(name, str)
                properties[name] = {"type": PY_TO_JSON_SCHEMA.get(py_type, "string")}
                if param.default is inspect.Parameter.empty:   # 没有默认值 → 必填
                    required.append(name)

            self._tools[fn.__name__] = {
                "fn": fn,
                "description": description,
                "parameters": {"type": "object", "properties": properties, "required": required},
            }
            return fn   # 装饰器必须返回原函数
        return decorator

    def manifest(self) -> str:
        """生成给模型看的工具说明书（JSON 格式，对齐 OpenAI tools 规范）。"""
        return json.dumps(
            [{ "name": name, "description": t["description"], "parameters": t["parameters"]}
             for name, t in self._tools.items()],
            ensure_ascii=False, indent=1)

    def execute(self, name: str, args: dict) -> str:
        """执行工具（带三层防护：存在性校验 → 入参校验 → 异常隔离）。"""
        if name not in self._tools:
            return f"错误：工具 {name} 不存在。可用：{list(self._tools)}"
        t = self._tools[name]
        # --- 入参校验：缺必填参数直接返回可读错误（模型看到错误能自行修正重试）---
        for req in t["parameters"]["required"]:
            if req not in args:
                return f"错误：缺少必填参数 {req}（类型 {t['parameters']['properties'][req]['type']}）"
        # --- 类型宽松校验：声明 integer 却传了 "123" 就帮忙转（模型经常传字符串数字）---
        cleaned = {}
        for k, v in args.items():
            want = t["parameters"]["properties"].get(k, {}).get("type")
            try:
                if want == "number" and isinstance(v, str):
                    v = float(v)
                elif want == "integer" and isinstance(v, str):
                    v = int(v)
            except (TypeError, ValueError):
                return f"错误：参数 {k} 应为 {want}，收到 {v!r}"
            cleaned[k] = v
        # --- 异常隔离：工具内部崩了返回错误字符串，绝不让 Agent 主循环跟着崩 ---
        try:
            return str(t["fn"](**cleaned))
        except Exception as e:
            return f"工具执行异常: {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# 用注册表定义本实验的工具集（每个 @tool 就是一个可插拔的能力）
# ---------------------------------------------------------------------------

registry = ToolRegistry()

@registry.tool(description="计算算术表达式，如 '23*47/2'。只支持数字和 + - * / ( )")
def calculate(expression: str) -> str:
    """安全计算器：白名单校验后求值（同 Lab 01）。"""
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expression):
        return "错误：表达式包含不允许的字符"
    return str(eval(expression))  # noqa: S307

@registry.tool(description="统计文本的中文字数与英文单词数")
def word_count(text: str) -> str:
    chinese = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    words = len(re.findall(r"[a-zA-Z]+", text))
    return f"中文字数={chinese}, 英文单词数={words}"

@registry.tool(description="生成指定长度的随机密码，长度 6-32")
def gen_password(length: int = 12) -> str:
    import random, string
    length = max(6, min(32, length))          # 参数范围裁剪：schema 之外的防线
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

@registry.tool(description="把摄氏温度转换为华氏温度，输入数字")
def c_to_f(celsius: float) -> str:
    return f"{celsius}°C = {celsius * 9 / 5 + 32:.1f}°F"


# ---------------------------------------------------------------------------
# Agent 循环（复用 Lab 01 的骨架，工具层换成注册表）
# ---------------------------------------------------------------------------

def llm(messages):
    return litellm.completion(
        model=f"openai/{MODEL}", api_base=GATEWAY, api_key="sk-labs-master",
        messages=messages, temperature=0, max_tokens=300,
    ).choices[0].message.content

def parse_json(raw: str) -> dict:
    text = re.sub(r"```[a-z]*|```", "", raw).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"action": "parse_error"}
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        try:
            return json.loads(m.group().replace("'", '"'))
        except json.JSONDecodeError:
            return {"action": "parse_error"}

SYSTEM = (
    "你是会使用工具的助手。工具清单（JSON）：\n" + registry.manifest() + "\n"
    '需要工具时只输出一行 JSON：{"action": "工具名", "args": {"参数名": "值"}}\n'
    '能给最终答案时只输出：{"action": "final_answer", "answer": "..."}\n'
    "不要输出 JSON 以外的内容。"
)

def run_agent(task: str, max_steps: int = 6) -> str:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    seen: dict[tuple, str] = {}
    parse_errors = 0            # 连续格式错误计数（实测：模型回显含特殊字符的结果时易触发）
    last_tool_result = None     # 最近一次成功的工具结果（降级出口用）
    for step in range(1, max_steps + 1):
        print(f"\n── 步骤 {step}")
        d = parse_json(llm(messages))
        print(f"   决策: {json.dumps(d, ensure_ascii=False)[:140]}")
        action = d.get("action")
        if action == "final_answer":
            return d.get("answer", "(无答案)")
        if action == "parse_error":
            parse_errors += 1
            # ── 降级策略（生产模式）：连续 2 次格式错误且手里已有工具结果 →
            #    不再纠结模型输出格式，直接把工具结果作为答案返回。
            #    实测场景：模型生成的密码含引号/特殊字符，回显进 JSON 时反复破坏格式。
            if parse_errors >= 2 and last_tool_result is not None:
                print("   ⚠️ 连续格式错误，降级返回最近一次工具结果")
                return f"{last_tool_result}（注：模型格式错误，已降级直接返回工具结果）"
            messages += [{"role": "user", "content": "格式错误，只输出一行 JSON"}]
            continue
        parse_errors = 0        # 成功解析一次就清零计数
        if action in registry._tools:
            args = d.get("args", {}) if isinstance(d.get("args"), dict) else {"expression": str(d.get("args", ""))}
            key = (action, json.dumps(args, sort_keys=True, ensure_ascii=False))
            if key in seen:
                messages += [{"role": "user",
                              "content": f"你已调用过 {action}({args})，结果 {seen[key]}。请直接给 final_answer。"}]
                continue
            result = registry.execute(action, args)
            seen[key] = result
            last_tool_result = result
            print(f"   工具 {action}{args} → {result}")
            messages += [{"role": "assistant", "content": json.dumps(d, ensure_ascii=False)},
                         {"role": "user", "content": f"工具返回：{result}"}]
        else:
            messages += [{"role": "user", "content": f"工具 {action} 不存在，可用：{list(registry._tools)}"}]
    return f"(达到最大步数 {max_steps})"

if __name__ == "__main__":
    tasks = sys.argv[1:] or [
        "帮我生成一个 16 位的随机密码",            # int 参数：考察 schema 传递
        "把 25 摄氏度转换成华氏度",              # float 参数
    ]
    for t in tasks:
        print(f"\n{'=' * 62}\n任务: {t}")
        print(f"✅ 最终答案: {run_agent(t)}")
