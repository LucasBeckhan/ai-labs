#!/usr/bin/env python3
"""
Lab 04 — 轻量 RAG 评估流水线
============================

**没有评估就没有 LLMOps。**

本脚本把 Lab 03 里"感觉 TOP_K=6 更好"这种主观感受，变成**可复现的量化指标**。
这是 LLMOps 与传统开发的分水岭：LLM 输出有随机性，任何参数/模型/prompt 的改动
都必须过同一套评估集对比，否则"变好/变坏"全靠猜。

三个指标（每个都对应 RAG 失败的一种模式）：
  1. 检索命中率 Recall@k —— 答案依据的文档有没有被检索进 top-k
     → 失败 = 检索层问题（分块/嵌入/TOP_K 要调）
  2. 忠实度（关键词校验版）—— 回答是否包含评估集要求的事实要点
     → 失败 = 生成层问题（模型能力/prompt 要改）
  3. 拒答正确性 —— 知识库外的问题是否老实说"没有"
     → 失败 = 幻觉，归因在模型能力（实测 0.5B 模型无法通过，与 TOP_K 无关）

生产级评估的演进方向：LLM-as-judge（用强模型打分）、ragas 框架、
线上真实问题回流进评估集 —— 但指标设计的骨架和这里完全一致。

运行：
  LITELLM_LOCAL_MODEL_COST_MAP=True ../.venv/bin/python -c "
  import eval_rag, rag_demo
  rag_demo.TOP_K = 3        # 换成 6 再跑一遍，对比指标
  eval_rag.main()"
"""
import os
import sys

# 把 Lab 03 的目录加入模块搜索路径 —— 评估脚本复用被测系统的代码，
# 这是评估流水线的标准做法：被测对象怎么部署，评估就怎么调用它，
# 避免"评估环境和生产环境行为不一致"的假象。
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab03-rag-basics"))
import rag_demo  # noqa: E402  复用 Lab 03 的索引/检索/生成

# ---------------------------------------------------------------------------
# 评估集（EVAL SET）：LLMOps 的"数据质量规则"，Quality of the answer 的 ground truth
# ---------------------------------------------------------------------------
# 每个用例包含四个字段，设计要点如下：
#   q        —— 问题。⚠ 必须"换一种问法"，不能抄知识库原文，
#               否则检索永远命中，指标失去区分度（这是新手最常犯的评估错误）。
#   source   —— 标准答案出自哪个文档（用来计算检索命中率）。
#   must     —— 标准回答必须包含的事实要点（关键词列表，用来校验忠实度）。
#   refusal  —— True 表示知识库中不存在答案：期望系统老实拒答。
#               越界题是评估集的"安全测试"，专测幻觉。
# 设计经验：答案题与越界题混合；覆盖每个知识文件；问题覆盖"事实型/推理型/否定型"。
EVAL_SET = [
    # --- 可回答：k8s-notes.md 中的事实 ---
    {"q": "HPA 缩容为什么要等一段时间？", "source": "k8s-notes.md", "must": ["稳定窗口"], "refusal": False},
    {"q": "Spark executor 是怎么启动的？", "source": "k8s-notes.md", "must": ["KubernetesExecutorBackend"], "refusal": False},
    {"q": "容器被 OOM 杀掉的退出码是多少？", "source": "k8s-notes.md", "must": ["137"], "refusal": False},
    # --- 可回答：llm-notes.md 中的事实 ---
    {"q": "vLLM 为什么比原生推理快？", "source": "llm-notes.md", "must": ["PagedAttention"], "refusal": False},
    {"q": "Text2SQL 的安全防线有哪些？", "source": "llm-notes.md", "must": ["只读"], "refusal": False},
    # --- 越界：知识库中没有 → 期望拒答（测幻觉） ---
    {"q": "珠穆朗玛峰有多高？", "source": None, "must": [], "refusal": True},
]


def main():
    """评估主流程：建索引 → 逐题"检索+生成" → 逐题打分 → 汇总指标表。"""
    col = rag_demo.build_index()          # 复用 Lab 03 的幂等建索引（重复运行不重灌）
    results = []

    for case in EVAL_SET:
        # ---- 第一步：检索（无论答案题还是越界题，都先走完整 RAG 链路）----
        hits = rag_demo.retrieve(col, case["q"])
        got_sources = {h["source"] for h in hits}    # 检索回来的来源文档集合

        # ---- 第二步 A：越界题 —— 只考察"是否老实拒答" ----
        if case["refusal"]:
            ans = rag_demo.answer(case["q"], hits)
            # 轻量判拒答：回答里出现"没有/无法"字样即视为拒答
            # （严格版应判断"回答内容是否与知识库无关"，这里保持简单）
            refused = ("没有" in ans) or ("无法" in ans)
            results.append({**case, "recall": None, "answer": ans, "pass_faithful": refused,
                            "note": "拒答正确" if refused else "❌ 幻觉！编造了知识库里没有的答案"})
            continue

        # ---- 第二步 B：答案题 —— 先算检索命中率，再生成并校验忠实度 ----
        # Recall@k 是"文档级"的粗指标：答案所在文档被检回即算命中。
        # ⚠ 它的盲区：文档命中 ≠ 包含答案的那个"块"命中 —— 文档级 100% 时
        #   忠实度仍可能只有 60%（实测），这就是需要块级/LLM-as-judge 的原因。
        recall = 1 if case["source"] in got_sources else 0

        ans = rag_demo.answer(case["q"], hits)
        # 忠实度（关键词校验版）：must 列表的关键词都出现在回答里才算通过。
        # ⚠ 局限：模型换同义说法会被误判；但对"数字/专有名词"类要点非常有效。
        faithful = all(kw in ans for kw in case["must"])

        # note 字段做"分层归因"：先分清是检索挂了还是生成挂了 ——
        # 归因错了，优化方向就会错（检索问题调模型是白费劲）。
        results.append({**case, "recall": recall, "answer": ans, "pass_faithful": faithful,
                        "note": "" if (recall and faithful) else "❌ " + ("检索未命中" if not recall else "要点缺失")})

    # ---- 第三步：汇总指标（只在"可回答题"上算 Recall/忠实度，越界题单独算拒答率）----
    answerable = [r for r in results if not r["refusal"]]
    n_answ = len(answerable)
    recall_hits = sum(r["recall"] for r in answerable)
    faithful_hits = sum(1 for r in answerable if r["pass_faithful"])
    refusal_ok = sum(1 for r in results if r["refusal"] and r["pass_faithful"])

    # ---- 第四步：输出报告（逐题明细 + 总分）----
    print(f"\n{'问题':<28} 检索  忠实  备注")
    print("-" * 66)
    for r in results:
        rec = "-" if r["recall"] is None else ("✅" if r["recall"] else "❌")
        fai = "✅" if r["pass_faithful"] else "❌"
        print(f"{r['q']:<30} {rec}     {fai}     {r['note']}")
    print("-" * 66)
    print(f"检索命中率 Recall@{rag_demo.TOP_K}: {recall_hits}/{n_answ} = {recall_hits / n_answ:.0%}")
    print(f"忠实度（要点齐全）:        {faithful_hits}/{n_answ} = {faithful_hits / n_answ:.0%}")
    print(f"拒答正确率:               {refusal_ok}/1")
    print("\n提示：改 rag_demo.TOP_K=3 和 =6 各跑一次，对比忠实度 —— 这就是 Lab 03 那个现象的量化版。")
    # 提醒：LLM 输出有随机性，同一次配置不同轮次可能一题一个对一个错
    # （实测踩过）——重要结论要多跑几轮取稳定值，别被单次噪声骗了。


if __name__ == "__main__":
    main()
