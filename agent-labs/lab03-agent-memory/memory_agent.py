#!/usr/bin/env python3
"""
Lab 03 — Agent 记忆：短期压缩与长期事实
========================================

【要解决的问题】上下文窗口有限（几 K~几百 K token），多轮长对话必然超窗。
生产 Agent 的记忆分两层（与人类类比）：
  短期记忆 = 上下文窗口里的对话历史 → 满了就"压缩"（旧轮次摘要成一句话）
  长期记忆 = 外部存储的事实（用户偏好/关键结论）→ 每轮注入，跨会话存在

本实验实现：
  ① 轮数上限触发的历史压缩（旧轮次 → LLM 摘要成一段"先前对话纪要"）
  ② 长期事实表（name→value），工具可读写；每轮注入 system prompt
  ③ 数据工程师视角：记忆就是"会话级明细 + 用户级汇总"——和数仓分层同构！

【运行前提】网关 localhost:4000
【运行】../.venv/bin/python memory_agent.py（内置三轮对话演示记忆效果）
"""
import json
import os
import re

import litellm

GATEWAY = os.environ.get("GATEWAY", "http://localhost:4000")
MODEL = os.environ.get("MODEL", "qwen-small")
MAX_TURNS_BEFORE_COMPRESS = 4      # 超过此轮数触发压缩（实验用小值便于观察）


def llm(messages, max_tokens=400):
    return litellm.completion(
        model=f"openai/{MODEL}", api_base=GATEWAY, api_key="sk-labs-master",
        messages=messages, temperature=0.3, max_tokens=max_tokens,
    ).choices[0].message.content


# ---------------------------------------------------------------------------
# 长期记忆：简单的 KV 事实表（生产会换成向量库/数据库 + 检索）
# ---------------------------------------------------------------------------
LONG_TERM: dict[str, str] = {}

def remember(name: str, value: str) -> str:
    LONG_TERM[name] = value
    return f"已记住 {name}={value}"

def recall(name: str) -> str:
    return LONG_TERM.get(name, "(没有这条记忆)")


# ---------------------------------------------------------------------------
# 短期记忆管理器：维护对话历史 + 超限压缩
# ---------------------------------------------------------------------------
class ConversationMemory:
    """短期记忆 = messages 列表 + 压缩策略。

    压缩算法（最常用的基线）：
      保留 system + 最近 N 轮原文，更早的轮次交给 LLM 摘要成一段"纪要"，
      之后用 [纪要 + 最近N轮] 继续对话。信息有损但窗口可控——
      这就是 ChatGPT 长对话"忘事"的原理，也和数仓"明细→汇总"完全同构。
    """

    def __init__(self, system_prompt: str):
        self.system = system_prompt
        self.rounds: list[tuple[str, str]] = []      # [(user, assistant)] 原文轮次
        self.summary = ""                            # 已压缩部分的摘要

    def add(self, user: str, assistant: str):
        self.rounds.append((user, assistant))

    def build_messages(self) -> list[dict]:
        """拼装发给 LLM 的最终上下文：system + [背景资料(长期记忆)] + 纪要 + 原文轮次。

        实测坑（重要）：把长期记忆写进 system prompt 时，小模型的注意力会被
        这段"显眼的事实"抢占——每个问题都回答那条记忆（复读机退化）。
        缓解：记忆用中性的"[背景资料]"消息注入 + 明确"仅在相关时使用"。
        根治：记忆按"与当前问题的相关性"选择性注入（RAG 检索记忆），而不是全量塞入。
        """
        msgs = [{"role": "system", "content": self.system}]
        if LONG_TERM:
            facts = "\n".join(f"  - {k}: {v}" for k, v in LONG_TERM.items())
            msgs.append({"role": "user",
                         "content": f"[背景资料，仅在相关时使用，不要主动复述]\n{facts}\n请回答用户的当前问题。"})
        if self.summary:
            msgs.append({"role": "user", "content": f"[先前对话纪要]{self.summary}"})
        for u, a in self.rounds:
            msgs.append({"role": "user", "content": u})
            msgs.append({"role": "assistant", "content": a})
        return msgs

    def maybe_compress(self) -> bool:
        """超过阈值就把最老的一半轮次压缩掉。返回是否发生了压缩。"""
        if len(self.rounds) <= MAX_TURNS_BEFORE_COMPRESS:
            return False
        old, self.rounds = self.rounds[:2], self.rounds[2:]   # 最老的 2 轮出列
        transcript = "\n".join(f"用户: {u}\n助手: {a}" for u, a in old)
        prompt = (f"把下面对话压缩成 3 句话以内的纪要（保留关键事实与结论）：\n{transcript}")
        self.summary = (self.summary + "\n" + llm([{"role": "user", "content": prompt}], max_tokens=120)).strip()
        print(f"   🗜️  短期记忆压缩：{len(old)} 轮 → 纪要追加（当前纪要 {len(self.summary)} 字）")
        return True


# ---------------------------------------------------------------------------
# 演示：多轮对话中两类记忆如何工作
# ---------------------------------------------------------------------------

SYSTEM = "你是一个有记忆的助手。回答尽量简短（两句话以内）。用户告诉你的重要偏好要主动确认。"

def chat(mem: ConversationMemory, user: str) -> str:
    reply = llm(mem.build_messages())
    mem.add(user, reply)
    mem.maybe_compress()
    return reply

if __name__ == "__main__":
    mem = ConversationMemory(SYSTEM)

    print("== 第 1 轮：写入长期记忆（显式 API）==")
    print("  ", remember("favorite_db", "StarRocks"))
    print("== 第 2 轮：对话（长期记忆已注入 system）==")
    print("  用户: 我最喜欢的数据库是什么？")
    print("  助手:", chat(mem, "我最喜欢的数据库是什么？"))

    print("== 第 3-6 轮：灌水对话，触发短期记忆压缩 ==")
    for i, q in enumerate(["今天天气怎么样？", "推荐一本书。", "再推荐一部电影。", "1+1=?"]):
        print(f"  用户: {q}")
        print("  助手:", chat(mem, q)[:60], "...")

    print("\n== 最终上下文结构（system + 纪要 + 原文轮次）==")
    for m in mem.build_messages():
        print(f"  [{m['role']}] {m['content'][:70].replace(chr(10), ' ')}")
    print("\n== 长期记忆表 ==", json.dumps(LONG_TERM, ensure_ascii=False))
