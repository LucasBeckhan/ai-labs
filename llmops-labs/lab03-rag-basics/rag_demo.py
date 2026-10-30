#!/usr/bin/env python3
"""
Lab 03 — 最小可用 RAG（检索增强生成）教学实现
================================================

本脚本演示 RAG 的完整链路，是理解所有 RAG 系统的"最小骨架"：

    ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌────────┐
    │ 知识文档 │ →  │ 分块      │ →  │ 嵌入入库 │ →  │ 检索 top-k│ →  │ LLM 生成│
    └─────────┘    └──────────┘    └─────────┘    └──────────┘    └────────┘
      knowledge/     chunk_text()    build_index()   retrieve()       answer()

四个阶段对应四个函数，每一处的质量都决定最终回答质量：
  - 分块(CHUNK_SIZE)太大 → 语义稀释；太小 → 上下文被切断
  - 嵌入模型必须与语言匹配（中文用 bge-m3），且查询/文档共用同一个模型
  - TOP_K 检索条数是"召回率 vs 噪声/成本"的权衡旋钮（Lab 04 用评估集量化过）

前置条件：
  1. ollama pull bge-m3              （嵌入模型，1.2GB）
  2. Lab 02 的 LiteLLM 网关运行中     （localhost:4000，生成走网关别名 qwen-small）
  3. 依赖已安装：chromadb litellm ollama（python 包）

运行：LITELLM_LOCAL_MODEL_COST_MAP=True ../.venv/bin/python rag_demo.py [问题1] [问题2]
"""
import glob
import os
import sys

import chromadb
import litellm
from chromadb.utils import embedding_functions

# ---------------------------------------------------------------------------
# 路径与常量：生产代码应全部走环境变量/配置文件（12-Factor 原则），
# 这里为了教学可读性用模块级常量。
# ---------------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))       # 本脚本所在目录（知识库/向量库都相对它定位）
DB_DIR = os.path.join(BASE, "chroma_db")                # 向量库持久化目录：删掉它 = 整个索引重建
COLLECTION = "labs_kb"                                  # chromadb 的集合名，类比"数据库里的一张表"

# ---- RAG 最重要的两个"数据工程"旋钮（Lab 04 用评估集量化过它们的影响）----
TOP_K = 3            # 检索条数。实测：3 会有问题漏检（忠实度 60%），6 更稳（80%）。改这里重跑 Lab 04 即可验证。
CHUNK_SIZE = 400     # 每个块的字符数（中文 ≈ 200~300 字）。过大稀释语义，过小切断上下文。
CHUNK_OVERLAP = 60   # 相邻块的重叠字符数：让跨块的句子在两个块里都完整出现，避免语义被切断。


def chunk_text(text: str) -> list[str]:
    """阶段一：分块。

    固定长度滑动窗口是最朴素的基线分块算法：
      - 每块 CHUNK_SIZE 个字符，相邻块重叠 CHUNK_OVERLAP 个字符；
      - 丢弃长度 < 30 的碎片（通常是末尾残句，检索价值极低）。

    为什么不用更智能的分块（按标题/语义/段落）？
      教学阶段先掌握基线，生产上再迭代 —— 任何分块策略的优劣都要靠
      Lab 04 的评估集来量化，而不是凭感觉。

    Args:
        text: 一个完整的 Markdown 文档内容。

    Returns:
        字符串列表，每个元素是一个"块"（将来对应向量库中的一条记录）。
    """
    chunks = []
    # 步进 = CHUNK_SIZE - CHUNK_OVERLAP：保证相邻块重叠 CHUNK_OVERLAP 个字符
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        piece = text[i:i + CHUNK_SIZE].strip()
        if len(piece) > 30:  # 过滤太碎的尾巴（如文档最后几个字）
            chunks.append(piece)
    return chunks


def build_index() -> chromadb.Collection:
    """阶段二：嵌入并入库（离线管道，通常定时/事件触发）。

    三个动作：
      1. 创建 OllamaEmbeddingFunction：chromadb 收到文本后自动调用
         Ollama 的 /api/embeddings 接口把文本变成向量（bge-m3，多语言模型）；
         ⚠ 查询和文档必须用同一个嵌入模型，否则向量不在同一空间，检索必然失败。
      2. PersistentClient：向量库落盘到 DB_DIR 目录（重启不丢）；
         换成 chromadb.Client() 则是内存态（Lab 06 容器里就是这么用的）。
      3. 增量处理：按"来源文件名"统计已入库块数，已处理过就跳过 ——
         重复运行脚本不会产生重复数据（这是所有 ETL 的基本要求：幂等）。

    Returns:
        chromadb.Collection：可用于检索的集合句柄。
    """
    # 嵌入函数：把文本 → 向量的"翻译器"。bge-m3 对中英文混合内容效果好。
    ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="bge-m3",
    )
    client = chromadb.PersistentClient(path=DB_DIR)
    col = client.get_or_create_collection(COLLECTION, embedding_function=ef)

    # 遍历 knowledge/ 下所有 Markdown 文件（换成你自己的文档目录即可复用）
    for path in sorted(glob.glob(os.path.join(BASE, "knowledge", "*.md"))):
        name = os.path.basename(path)                 # 文件名作为元数据，检索后能溯源"答案出自哪份文档"
        text = open(path, encoding="utf-8").read()
        chunks = chunk_text(text)

        # --- 增量判断：该文件已入库的块数 >= 现在应入库的块数 → 视为已处理 ---
        # （严格做法还会比对内容 hash，教学版用块数近似；改了 CHUNK_SIZE 要手动删 chroma_db 重建）
        existing = col.get(where={"source": name})
        if existing["ids"] and len(existing["ids"]) >= len(chunks):
            print(f"[skip] {name} 已入库 {len(existing['ids'])} 块")
            continue
        if existing["ids"]:
            col.delete(ids=existing["ids"])           # 文件被编辑过（块数变少）→ 先删旧块再重灌

        # 入库三件套：ids（唯一标识）、documents（原文，chromadb 会自动调 ef 转向量）、
        # metadatas（元数据：source/chunk 序号，检索结果里用来溯源）
        col.add(
            ids=[f"{name}#{i}" for i in range(len(chunks))],
            documents=chunks,
            metadatas=[{"source": name, "chunk": i} for i in range(len(chunks))],
        )
        print(f"[ok] {name} 入库 {len(chunks)} 块")
    return col


def retrieve(col: chromadb.Collection, question: str) -> list[dict]:
    """阶段三：检索 —— 把用户问题也转成向量，在向量空间里找最近的 TOP_K 块。

    "语义检索"的本质：query 和 document 各自变成向量后，
    "意思相近" 就变成了 "向量距离近"（默认用余弦/欧氏距离，由集合创建时决定）。

    注意：chromadb 的 query() 会自动用集合创建时绑定的同一个嵌入函数处理 question，
          这就保证了查询/文档向量在同一空间（见 build_index 里的警告）。

    Args:
        col: 已建好索引的集合。
        question: 用户问题。

    Returns:
        检索结果列表，每项含：text（块原文）、source（来源文件）、distance（距离，越小越相关）。
    """
    res = col.query(query_texts=[question], n_results=TOP_K)
    # zip 把三个平行列表（文本/元数据/距离）组装成好读的字典
    return [
        {"text": doc, "source": meta["source"], "distance": dist}
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def answer(question: str, hits: list[dict]) -> str:
    """阶段四：生成 —— 把检索到的片段作为"参考资料"拼进 prompt，让 LLM 基于它们回答。

    这就是 RAG 里的 A（Augmented，增强）：模型的回答被"增强"到了你的私有知识上，
    而不是只依赖训练时见过的公开数据 —— 既治幻觉、又可溯源。

    prompt 工程要点：
      - 明确约束"只根据参考资料回答，没有就说没有"（防幻觉的指令，小模型不总遵守，见 Lab 04）；
      - 每个片段标注来源 [文件名]，回答可以引用出处。

    Args:
        question: 用户问题。
        hits: retrieve() 的结果。

    Returns:
        模型生成的回答文本。
    """
    context = "\n---\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    prompt = (
        "你是知识库助手。只根据下面的参考资料回答问题；"
        "如果资料里没有答案，就明确说\"知识库中没有\"。\n\n"
        f"参考资料：\n{context}\n\n问题：{question}"
    )
    # 走 Lab 02 的 LiteLLM 网关而不是直连 Ollama：
    #   - model 带 "openai/" 前缀 = 用 OpenAI 协议调网关的别名（网关再路由到具体模型）
    #   - 不带前缀 litellm 会试图猜 provider 而报错（实测踩过）
    resp = litellm.completion(
        model="openai/qwen-small",
        api_base="http://localhost:4000",
        api_key="sk-labs-master",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,      # RAG 回答要贴资料，低温求稳
        max_tokens=512,       # ⚠ 生产必设：实测不设上限时 0.5B 小模型可能无限生成
                              #   （单次跑出 1.8 万 token 直接卡死流水线）
    )
    return resp.choices[0].message.content


def main():
    """入口：建索引 → 依次回答命令行传入的问题（未传则用两个默认问题演示）。"""
    col = build_index()
    questions = sys.argv[1:] or ["HPA缩容为什么要等一段时间？", "vLLM 为什么比原生推理快？"]
    for q in questions:
        print(f"\n{'=' * 60}\nQ: {q}")
        hits = retrieve(col, q)
        # 打印检索明细：来源 + 距离 + 块开头 —— 看懂这三行才能判断"检索层"有没有问题
        # （回答错了先看这里：块没检进来 = 检索问题；块对了答错 = 生成问题）
        for i, h in enumerate(hits, 1):
            print(f"  [{i}] {h['source']} (距离 {h['distance']:.3f}) {h['text'][:40]}...")
        print(f"A: {answer(q, hits)}")


if __name__ == "__main__":
    main()
