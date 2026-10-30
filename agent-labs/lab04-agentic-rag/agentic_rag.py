#!/usr/bin/env python3
"""
Lab 04 — Agentic RAG：会"自己决定何时检索"的 RAG
==================================================

【与普通 RAG（llmops-labs Lab03）的本质区别】
普通 RAG 是"流水线"：每次提问 → 无脑检索 → 拼上下文 → 回答。
Agentic RAG 把"检索"变成 Agent 的一个**工具**，由模型决策：
  ① 这个问题需要查知识库吗？（闲聊/计算就不查——省钱省时延）
  ② 用什么关键词查？（查询改写：把口语问题改成检索友好的关键词）
  ③ 检索结果不够好要不要换个关键词重查？（自我反思重试）
  ④ 都不满意时老实拒答

这就是 2024-2026 业界 RAG 演进的主线：**pipeline → agentic**。

【运行前提】
  ① 网关 localhost:4000；② Ollama 的 bge-m3 已拉取；
  ③ 复用 llmops-labs/lab03 的知识库与检索函数（sys.path 导入）。
【运行】../.venv/bin/python agentic_rag.py
"""
import json
import os
import re
import sys

# 复用 llmops-labs Lab03 的索引与检索（被测组件复用，和评估脚本同一套路）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "llmops-labs", "lab03-rag-basics"))
import rag_demo  # noqa: E402  提供 build_index() / retrieve()

import litellm  # noqa: E402

GATEWAY = os.environ.get("GATEWAY", "http://localhost:4000")
MODEL = os.environ.get("MODEL", "qwen-strong")     # 查询改写需要一点指令遵循能力，默认用 1.5B


def llm(messages, max_tokens=300):
    return litellm.completion(
        model=f"openai/{MODEL}", api_base=GATEWAY, api_key="sk-labs-master",
        messages=messages, temperature=0, max_tokens=max_tokens,
    ).choices[0].message.content


def parse_json(raw: str) -> dict:
    text = re.sub(r"```[a-z]*|```", "", raw).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        try:
            return json.loads(m.group().replace("'", '"'))
        except json.JSONDecodeError:
            return {}


# ---------------------------------------------------------------------------
# Agentic RAG 主流程：三阶段决策
# ---------------------------------------------------------------------------

def decide_need_retrieval(question: str) -> bool:
    """阶段①：这个问题需要查知识库吗？（省掉不必要的检索）"""
    d = parse_json(llm([
        {"role": "system", "content":
         '判断用户问题是否需要查询"K8s/LLM 技术知识库"才能回答。只输出 JSON：'
         '{"need": true/false, "reason": "一句话"}。闲聊、计算、常识类问题不需要。'},
        {"role": "user", "content": question},
    ], max_tokens=80))
    print(f"   ① 检索决策: {json.dumps(d, ensure_ascii=False)[:80]}")
    return bool(d.get("need"))


def rewrite_query(question: str) -> str:
    """阶段②：查询改写——把口语问题变成检索友好的关键词组合。

    例："容器被杀 exit 137 是怎么回事" → "OOMKilled 137 原因"
    检索质量对用词极敏感，这一步往往是 Agentic RAG 最大的增益来源。
    """
    d = parse_json(llm([
        {"role": "system", "content":
         '把用户问题改写成适合向量检索的关键词查询（保留英文术语原文，如 OOMKilled/checkpoint）。'
         '只输出 JSON：{"query": "..."}'},
        {"role": "user", "content": question},
    ], max_tokens=80))
    q = d.get("query", question)
    print(f"   ② 查询改写: {question!r} → {q!r}")
    return q


def answer_with_reflection(question: str, col, max_retries: int = 2) -> str:
    """阶段③：检索 → 生成 → （可选）自我反思重查。"""
    query = rewrite_query(question)
    for attempt in range(1, max_retries + 1):
        hits = rag_demo.retrieve(col, query)
        print(f"   ③ 检索(第{attempt}轮): top1 距离 {hits[0]['distance']:.3f} 来源 {hits[0]['source']}")
        context = "\n---\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
        raw = llm([
            {"role": "system", "content":
             "根据参考资料回答。如果资料与问题不相关，只输出 JSON：{\"retry\": true, \"better_query\": \"更好的检索词\"}；"
             '相关则输出 {"retry": false, "answer": "回答"}'},
            {"role": "user", "content": f"参考资料：\n{context}\n\n问题：{question}"},
        ])
        d = parse_json(raw)
        if not d.get("retry"):
            return d.get("answer", raw[:200])
        better = d.get("better_query")
        print(f"   ↻ 自我反思：资料不相关，换检索词重查 → {better!r}")
        if better:
            query = better
    return "（多次检索后仍无相关资料：知识库中没有该问题的答案）"


def agentic_rag(question: str, col) -> str:
    print(f"\n{'=' * 62}\n问题: {question}")
    if not decide_need_retrieval(question):
        return llm([{"role": "user", "content": question}])       # 不查库，直接答
    return answer_with_reflection(question, col)


if __name__ == "__main__":
    col = rag_demo.build_index()          # 幂等建索引（llmops lab03 的知识库）
    for q in ["容器被 OOM 杀掉的退出码是多少？",   # 需要检索 + 可能需要改写
              "1+1 等于几？",                        # 不需要检索（省一次检索+改写的成本）
              "什么是 PagedAttention？"]:            # 术语在库里，直接命中
        print(f"\n✅ 答案: {agentic_rag(q, col)}")
