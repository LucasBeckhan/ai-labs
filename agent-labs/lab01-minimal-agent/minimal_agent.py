#!/usr/bin/env python3
"""
Lab 01 — 最小 Agent：从零实现 ReAct 循环（不用任何框架）
=========================================================

【这 100 行代码揭示的事实】
所有 Agent 框架（LangChain/LangGraph/AutoGen...）的核心都是一个循环：

    ┌──────────────────────────────────────────────┐
    │  while True:                                 │
    │      ① 把"任务 + 工具清单 + 历史"发给 LLM      │
    │      ② LLM 回答两种可能：                     │
    │         a) {"action": "工具名", "input": ...}  │──→ 执行工具，结果记入历史
    │         b) {"action": "final_answer", ...}    │──→ 跳出循环，任务完成
    └──────────────────────────────────────────────┘

  这就是 ReAct（Reasoning + Acting）模式：模型"想一想"（要不要用工具）
  再"动一手"（调用工具），观察结果后再决定下一步。

【为什么用 prompt 让模型输出 JSON，而不是用"原生 function calling"？】
  1. 教育：你能亲手看到框架在底层做的事——拼 prompt、解析输出、维护历史；
  2. 通用：任何模型（哪怕 0.5B）都能跑，不依赖模型是否支持 tool_calls；
  3. 可控：解析逻辑在你手里，出问题你能修。

【运行前提】Lab 02 的 LiteLLM 网关在 localhost:4000（llmops-labs/lab02 启动）
【运行方式】bash run.sh "算一下 23 乘以 47 再除以 2"（自动使用项目虚拟环境）
"""
import json
import os
import re
import sys

# macOS的Python可能从系统网络设置读取代理，即使终端没设置HTTP_PROXY。
# 本机模型网关应直接连接；保留用户已有的代理例外，不关闭外部请求的代理。
_proxy_exclusions = os.environ.get("no_proxy", os.environ.get("NO_PROXY", "")).split(",")
for _host in ("localhost", "127.0.0.1", "::1"):
    if _host not in _proxy_exclusions:
        _proxy_exclusions.append(_host)
_no_proxy = ",".join(item for item in _proxy_exclusions if item)
os.environ["NO_PROXY"] = os.environ["no_proxy"] = _no_proxy
# 本地实验使用内置价格表，避免import时额外联网；可用环境变量显式覆盖。
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

try:
    import litellm
except ModuleNotFoundError as exc:
    if exc.name != "litellm":
        raise
    from pathlib import Path
    project_python = Path(__file__).resolve().parents[2] / "llmops-labs/.venv/bin/python"
    raise SystemExit(
        f"当前解释器 {sys.executable} 未安装 litellm。\n"
        f"请将 PyCharm 运行解释器设为：{project_python}\n"
        "也可在本章目录执行：bash run.sh"
    ) from None

# ---------------------------------------------------------------------------
# 第 0 部分：LLM 调用封装（走 LiteLLM 网关，与 llmops-labs 保持一致）
# ---------------------------------------------------------------------------

GATEWAY = os.environ.get("GATEWAY", "http://localhost:4000")
API_KEY = os.environ.get("API_KEY", "sk-labs-master")
MODEL = os.environ.get("MODEL", "qwen-small")       # 网关别名（小而快，适合教学；卡住就换 qwen-strong）


def llm(messages: list[dict]) -> str:
    """调用一次 LLM。messages 是 OpenAI 格式的对话历史。"""
    resp = litellm.completion(
        model=f"openai/{MODEL}",          # openai/ 前缀 = 用 OpenAI 协议调网关别名
        api_base=GATEWAY,
        api_key=API_KEY,
        messages=messages,
        temperature=0,                    # Agent 决策要确定性：同样的输入走同样的路
        max_tokens=300,                   # 限制输出长度：决策 JSON 不需要长篇大论
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# 第 1 部分：工具定义 —— Agent 的"手"
# 每个工具 = 名字 + 描述（给模型看的"说明书"）+ 一个普通 Python 函数
# 工具好不好用，90% 取决于描述写得清不清楚（模型靠描述决定何时调用）
# ---------------------------------------------------------------------------

def tool_calculate(expression: str) -> str:
    """安全计算器：只允许数字和 + - * / ( ) 空格，其他字符一律拒绝。

    为什么不直接 eval()？—— eval 会执行任意代码，模型生成的表达式
    若包含 __import__ 之类的注入内容就是安全事故。白名单校验是底线。
    """
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expression):
        return "错误：表达式包含不允许的字符"
    try:
        # 白名单通过后，eval 的输入已被约束成纯算术——安全
        return str(eval(expression))  # noqa: S307（输入已白名单校验）
    except Exception as e:
        return f"计算失败: {e}"


def tool_word_count(text: str) -> str:
    """中英文字数统计（英文按词、中文按字）。"""
    chinese = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    words = len(re.findall(r"[a-zA-Z]+", text))
    return f"中文字数={chinese}, 英文单词数={words}"


def tool_now(dummy: str = "") -> str:
    """返回当前时间（dummy 参数仅为统一工具签名，模型会传空串）。"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 工具注册表：名字 → 函数。Lab 02 会把它升级成"带 JSON Schema 的注册表"
TOOLS = {
    "calculate": {"fn": tool_calculate, "desc": "计算算术表达式，如 '23*47/2'。只支持数字和加减乘除括号"},
    "word_count": {"fn": tool_word_count, "desc": "统计一段文本里中文字数和英文单词数"},
    "now": {"fn": tool_now, "desc": "获取当前日期时间"},
}


# ---------------------------------------------------------------------------
# 第 2 部分：Agent 循环 —— Agent 的"脑"
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    """拼装系统提示词：告诉模型它是谁、有哪些工具、必须按什么格式输出。

    格式约定是整个循环的契约：
      想用工具 → 输出一行 JSON：{"action": "工具名", "input": "工具入参"}
      想回答   → 输出一行 JSON：{"action": "final_answer", "answer": "最终答案"}
    """
    tool_lines = "\n".join(f"- {name}: {t['desc']}" for name, t in TOOLS.items())
    return (
        "你是一个会使用工具的助手。你可以使用以下工具：\n"
        f"{tool_lines}\n\n"
        "规则：\n"
        '1. 需要工具时，只输出一行 JSON：{"action": "工具名", "input": "工具入参"}\n'
        '2. 能给出最终答案时，只输出一行 JSON：{"action": "final_answer", "answer": "答案"}\n'
        "3. 不要输出 JSON 以外的任何文字（不要解释、不要 markdown）\n"
        "4. 计算类问题必须调用 calculate 工具，不要自己心算"
    )


def parse_decision(raw: str) -> dict:
    """从模型输出里解析出决策 JSON。

    小模型经常"不守规矩"：输出多余文字/markdown/单引号 JSON。
    解析器要做三件事：剥 markdown 壳 → 找到第一个 {...} → 容错解析。
    解析失败返回 {"action": "parse_error"}，由主循环重试——
    这就是框架里"输出修复器"(output parser) 的原型。
    """
    text = re.sub(r"```[a-z]*|```", "", raw).strip()          # 剥掉可能的 markdown 代码块
    match = re.search(r"\{.*\}", text, re.DOTALL)             # 找到第一段大括号内容
    if not match:
        return {"action": "parse_error", "raw": raw[:100]}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        # 常见容错：模型用了单引号 → 粗暴替换成双引号再试一次
        try:
            return json.loads(match.group().replace("'", '"'))
        except json.JSONDecodeError:
            return {"action": "parse_error", "raw": raw[:100]}


def run_agent(task: str, max_steps: int = 6) -> str:
    """Agent 主循环。

    Args:
        task: 用户的任务描述。
        max_steps: 最大步数——防止小模型死循环（框架里叫 recursion_limit）。

    Returns:
        最终答案字符串。
    """
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": task},
    ]
    # 循环检测器：记录 (工具名, 入参) 出现过的"最终结果"。
    # 实测小模型的经典失败模式 = 反复调用同一工具拿同一结果，永远不切换到 final_answer。
    # 检测到重复时，把结果直接"塞回"并强提示"请给最终答案"——一行代码救活死循环。
    seen_results: dict[tuple, str] = {}

    for step in range(1, max_steps + 1):
        print(f"\n── 步骤 {step}：思考中 ...")
        decision = parse_decision(llm(messages))
        print(f"   决策: {json.dumps(decision, ensure_ascii=False)[:120]}")

        action = decision.get("action")

        if action == "final_answer":
            return decision.get("answer", "(模型没给答案)")

        if action == "parse_error":
            # 解析失败：把"格式错了"反馈给模型重试（而不是直接崩）
            messages.append({"role": "assistant", "content": decision.get("raw", "")})
            messages.append({"role": "user", "content": '格式错误，请只输出一行 JSON：{"action": ...}'})
            continue

        if action in TOOLS:
            tool_input = str(decision.get("input", ""))
            key = (action, tool_input)
            if key in seen_results:
                # ── 循环检测命中：同一工具同一入参已执行过 → 不再重复执行，
                #    直接把历史结果 + 明确指令反馈给模型（比 max_steps 硬断优雅得多）
                result = seen_results[key]
                print(f"   ⚠️ 检测到重复调用，注入纠偏提示")
                messages.append({"role": "user",
                                 "content": f"你已调用过 {action}({tool_input})，结果是 {result}。"
                                            '请直接输出 {"action": "final_answer", "answer": "..."} 给出最终答案。'})
                continue
            result = TOOLS[action]["fn"](tool_input)          # ← 真正"动手"的地方
            seen_results[key] = result
            print(f"   工具 {action}({tool_input!r}) → {result}")
            # 把工具结果追加进历史：模型下一轮"观察"到的就是它
            messages.append({"role": "assistant", "content": json.dumps(decision, ensure_ascii=False)})
            messages.append({"role": "user", "content": f"工具返回：{result}"})
        else:
            # 模型幻觉出一个不存在的工具 → 明确告知可用工具（幻觉治理的最小手段）
            messages.append({"role": "user",
                             "content": f"工具 {action} 不存在。可用工具：{list(TOOLS)}"})

    return f"(达到最大步数 {max_steps}，任务未完成——真实场景要考虑放弃或升级模型)"


# ---------------------------------------------------------------------------
# 第 3 部分：入口 —— 三类测试任务（工具型 / 直答型 / 混合型）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tasks = sys.argv[1:] or [
        "算一下 23 乘以 47 再除以 2",          # 单工具任务
        "统计这句话里有多少个字：大数据与人工智能正在融合",  # 另一个工具
        "用一句话介绍什么是 Kubernetes",        # 无需工具，考察模型会不会正确给 final_answer
    ]
    for t in tasks:
        print(f"\n{'=' * 62}\n任务: {t}")
        answer = run_agent(t)
        print(f"\n✅ 最终答案: {answer}")
