#!/usr/bin/env python3
"""
Lab 06 毕业项目 — RAG 服务（容器化部署进 Kubernetes）
=====================================================

和 Lab 03 的单机脚本相比，完成了从"脚本"到"服务"的工程化三步：

  1. 进程化    ：FastAPI 提供 /query HTTP 接口 —— 不再是一次性脚本，
                而是可以被 K8s 调度、被多用户并发访问的常驻服务
  2. 可观测    ：/metrics 暴露 Prometheus 指标（请求计数 + 累计耗时），
                被 K8s 集群里的 Prometheus 通过"注解发现"自动抓取（零配置接入）
  3. 配置化    ：模型地址/名字/检索条数全部走环境变量（12-Factor 原则）——
                同一个镜像改环境变量就能换模型，TOP_K 直接采用 Lab 04 评估结论

部署拓扑（为什么代码里有 host.docker.internal）：

    本机 curl ─→ localhost:8080 ─[kind 端口映射]─→ NodePort 30080
                                                    │
                                            RAG Pod（hostNetwork）
                                            ├─ /query  检索 + 生成
                                            └─ /metrics ← Prometheus 自动抓取
                                                    │
                              host.docker.internal:11434（宿主机 Ollama）
                                                    │
                                          bge-m3 嵌入 + qwen2.5 生成

运行（本地冒烟）：docker run -p 18000:8000 -e OLLAMA_URL=http://host.docker.internal:11434 rag-service:v1
"""
import os
import time
from pathlib import Path

import chromadb
import ollama
from chromadb.utils import embedding_functions
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

# ---------------------------------------------------------------------------
# 环境变量配置（12-Factor 原则）：同一个镜像，改环境变量就能切换模型/知识库/检索条数
# ---------------------------------------------------------------------------
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
# host.docker.internal 是 Docker Desktop 的特殊域名：容器通过它访问宿主机（Mac）上的服务。
# ⚠ 前提：宿主机 Ollama 必须 OLLAMA_HOST=0.0.0.0 启动（默认只监听 127.0.0.1，容器连不到）
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")             # 嵌入模型（多语言，中文效果好）
GEN_MODEL = os.environ.get("GEN_MODEL", "qwen2.5:0.5b-instruct")  # 生成模型
TOP_K = int(os.environ.get("TOP_K", "6"))   # 检索条数：Lab 04 评估的结论（6 优于 3）——评估结果变成部署配置
KB_DIR = Path(os.environ.get("KB_DIR", "/app/knowledge"))         # 知识库目录（构建时 COPY 进镜像）
CHUNK, OVERLAP = 400, 60                                          # 分块大小与重叠（与 Lab 03 一致）

app = FastAPI()
REQS = 0          # 累计请求数（计数器指标，Prometheus 的 rate() 基于它算 QPS）
LATENCY_MS = 0.0  # 累计推理耗时 ms（除以请求数 = 平均延迟——AI 服务核心 SLI）
# ⚠ 必须显式指定 host：ollama 包默认连 127.0.0.1，在容器里指向容器自己，必然 ConnectionError（实测踩过）
AI = ollama.Client(host=OLLAMA_URL)


def chunk_text(text: str) -> list[str]:
    """分块：与 Lab 03 相同的滑动窗口算法（保持两个 Lab 的行为一致，便于对照学习）。"""
    return [t for t in (text[i:i + CHUNK].strip() for i in range(0, len(text), CHUNK - OVERLAP)) if len(t) > 30]


def build_index() -> chromadb.Collection:
    """启动时构建向量索引（FastAPI import 阶段执行一次，之后常驻内存）。

    三个与 Lab 03 不同的工程决策：
      1. chromadb.Client()（内存态）而非 PersistentClient —— 知识库只有 8 个块，
         重建索引秒级完成，省去挂载持久卷的复杂度；知识库大了以后应挂 PVC + PersistentClient
         （演进方案见 Lab 06 文档"观察与思考"）；
      2. 嵌入函数指向 OLLAMA_URL（环境变量），而不是写死 localhost —— 容器里 localhost 是容器自己；
      3. 集合名 rag_kb —— chromadb 要求集合名 ≥3 字符（"kb" 会报 Validation error，实测踩过）。
    """
    ef = embedding_functions.OllamaEmbeddingFunction(url=f"{OLLAMA_URL}/api/embeddings", model_name=EMBED_MODEL)
    client = chromadb.Client()  # 容器内用内存态即可（重启重建，索引秒级）；持久卷方案见文档思考题
    col = client.get_or_create_collection("rag_kb", embedding_function=ef)
    docs, ids, metas = [], [], []
    for path in sorted(KB_DIR.glob("*.md")):
        for i, c in enumerate(chunk_text(path.read_text(encoding="utf-8"))):
            docs.append(c)
            ids.append(f"{path.name}#{i}")
            metas.append({"source": path.name})   # 元数据带来源：回答里能展示"依据哪份文档"
    if docs:
        col.add(ids=ids, documents=docs, metadatas=metas)   # 一次批量写入（比逐条 add 快）
    return col


# 模块级执行 = 进程启动时建索引（uvicorn import main 时触发）。
# 失败会让容器启动失败（K8s 的 readiness/liveness 会如实反映）——这是"快速失败"的正确姿势。
COL = build_index()


@app.get("/query")
def query(q: str):
    """主接口：RAG 全链路（检索 → 拼 prompt → 生成 → 返回答案与来源）。

    与 Lab 03 单机脚本的两点差异：
      1. 输入输出走 HTTP（q 是 URL 参数），可被任何语言/系统调用；
      2. 每次请求累计 REQS/LATENCY_MS —— 这是 /metrics 的数据来源，
         也是"AI 服务可观测性"的最小实现（生产可换 prometheus_client 库）。

    Args:
        q: 用户问题（URL 查询参数，中文会被自动 URL 编码/解码）。

    Returns:
        JSON: {"answer": 生成的回答, "sources": 来源文档列表}。
    """
    global REQS, LATENCY_MS
    t0 = time.time()
    # ① 检索：向量库返回 TOP_K 个最相关块
    hits = COL.query(query_texts=[q], n_results=TOP_K)
    # ② 增强：把检索到的块拼成"参考资料"段（与 Lab 03 的 prompt 模板一致）
    context = "\n---\n".join(hits["documents"][0])
    prompt = (f"只根据参考资料回答，没有就说\"知识库中没有\"。\n\n参考资料：\n{context}\n\n问题：{q}")
    # ③ 生成：通过 AI client（host=OLLAMA_URL）调用宿主机 Ollama
    #    ⚠ 生产建议给 chat 加超时与 max_tokens（Lab 03 的无限生成教训在这里同样适用）
    resp = AI.chat(model=GEN_MODEL, messages=[{"role": "user", "content": prompt}])
    # ④ 记录指标（进程内计数；多副本部署时每副本独立计数，Prometheus 会按实例聚合）
    REQS += 1
    LATENCY_MS += (time.time() - t0) * 1000
    return {"answer": resp["message"]["content"], "sources": hits["metadatas"][0]}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """Prometheus 抓取端点（文本格式）。

    格式约定：# HELP/TYPE 两行元信息 + "指标名 值" 的样本行。
    K8s 集群里的 Prometheus 通过 Pod 的注解（prometheus.io/scrape=true）发现本服务，
    并按注解里的 port/path 抓取 /metrics —— 应用代码只需要"把指标吐出来"。
    生产进阶：换 prometheus_client 库（自动处理格式/多线程安全/直方图分桶）。
    """
    return (
        "# HELP rag_requests_total total rag queries served\n"
        "# TYPE rag_requests_total counter\n"
        f"rag_requests_total {REQS}\n"
        "# HELP rag_latency_ms_sum cumulative inference latency in ms\n"
        "# TYPE rag_latency_ms_sum counter\n"
        f"rag_latency_ms_sum {LATENCY_MS:.0f}\n"
    )
