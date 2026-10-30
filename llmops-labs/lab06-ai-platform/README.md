# Lab 06 — 毕业项目：把 RAG 服务部署成 K8s 里的 AI 服务（全链路观测）

> ✅ 已在本机完整验证：RAG 服务容器化 → kind 集群 → NodePort 调用 → 回答 + Prometheus 自动发现并采集指标。
> 这是"从模型接入到 K8s 部署监控的完整 LLMOps 链路"的可运行实物。

## 📖 本章学习指导

> 建议时长 **4 小时（分两次）** ｜ 前置：Lab 02/03 + K8s 全部 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q1/Q3 ｜ **毕业项目**

**学习循环：**
1. **读**（20min）：架构图 + 三个关键设计决策（hostNetwork/环境变量化/指标先行）
2. **跑**（90min）：容器冒烟 → 部署进 kind → NodePort 调用 → **Prometheus 自动发现** → Grafana 画图
3. **破坏练习**（30min）：① 集合名改回 "kb"（<3 字符）看启动报错；② 不传 OLLAMA_URL 看连接错误（ollama 包默认 127.0.0.1）
4. **验收自测**：① LLM 应用上 K8s 三个不同？② hostNetwork 的作用与代价？③ /metrics 为什么这样设计？
5. **产出**：三件套截图（查询结果/Prometheus target up/Grafana 曲线）——**你的 LLMOps 实物证据**

## 架构（画得出来的才叫懂）

```
本机 curl ──> localhost:8080 ──[kind 端口映射]──> NodePort 30080
                                                    │
                                              RAG Pod (hostNetwork)
                                              ├─ /query  检索 + 生成
                                              └─ /metrics  ← Prometheus 注解发现自动抓取
                                                    │
                                              host.docker.internal:11434
                                                    │
                                              宿主机 Ollama（bge-m3 嵌入 + qwen 生成）
```

**关键设计决策**：
1. **hostNetwork: true** —— Pod 共享节点网络栈，这样 `host.docker.internal` 才能解析到宿主机，访问跑在 Mac 上的 Ollama。生产里模型服务本来就是集群内 Pod（Lab 08 的 vLLM），这个"访问宿主机"的桥接只是单机实验的形态，但 hostNetwork 本身是真实的生产技术（节点端口占用、端口冲突的根源）。
2. **配置全部环境变量化**（OLLAMA_URL/EMBED_MODEL/GEN_MODEL/TOP_K）—— 同一镜像改环境变量就能切模型；`TOP_K=6` 直接来自 Lab 04 的评估结论，**评估结果变成部署配置**，这就是评估驱动的 LLMOps。
3. **指标先行**：/metrics 暴露 `rag_requests_total`（请求数）和 `rag_latency_ms_sum`（累计耗时），Prometheus 用 k8s-labs Lab 10 的注解发现机制自动抓取 —— 没有写一行抓取配置。

## 核心问答

**Q1：LLM 应用上 K8s 和普通应用有什么不同？**

> 参考答法：三点不同。① **依赖重**：模型和向量库要么打进镜像（体积 GB 级），要么外置成服务 —— 我的方案是模型外置（Ollama/vLLM 独立服务）、知识库内嵌（索引秒级重建）；② **响应慢且不确定**：推理秒级起步，readiness 探针要选轻量路径（/metrics），超时要给足；③ **指标不同**：除了 QPS/延迟，还要 token 数、首 token 延迟（TTFT）、显存利用率 —— 这些才是 AI 服务的核心 SLI。

**Q2：RAG 服务的容量怎么规划？**

> 参考答法：拆三段算。检索段：向量库 CPU/内存与索引规模相关（百万级向量几 GB 内存）；生成段：吞吐由模型推理服务决定（GPU 场景看 KV Cache 容量，Lab 08）；整体：我的 /metrics 暴露累计耗时，`Δrag_latency_ms_sum / Δrag_requests_total` 就是平均延迟 —— HPA 的指标可以直接挂这个自定义指标（KEDA）。

**Q3：怎么从单机走向生产拓扑？**

> 参考答法：把"宿主机 Ollama"换成集群内模型服务（vLLM Deployment + GPU 节点池 + Service），RAG 服务通过 Service DNS 调用；网关（Lab 02 的 LiteLLM）作为独立 Deployment 挡在应用与模型之间做多模型路由和配额；Prometheus 换成 kube-prometheus-stack。**架构不变，只是每个方框都变成集群内的高可用副本** —— 本实验验证的就是这个骨架。

## 动手实验

### 1. 构建镜像（首次约 3 分钟）

```bash
cd llmops-labs/lab06-ai-platform/rag_service
cp -r ../lab03-rag-basics/knowledge .       # 复用 Lab 03 的知识库
docker build -t rag-service:v1 .            # python:3.12-slim 基础（记得先走镜像站拉取）
# 本机冒烟：模型地址指向宿主机 Ollama
docker run --rm -d --name rag-test -p 18000:8000 -e OLLAMA_URL=http://host.docker.internal:11434 rag-service:v1
curl -s "http://localhost:18000/query?q=容器被OOM杀掉的退出码是多少"   # 实测：退出码是137
curl -s http://localhost:18000/metrics | grep rag_                   # rag_requests_total 1
docker rm -f rag-test
```

### 2. 宿主机 Ollama 开放到容器网络（一次性）

```bash
pkill -f "ollama serve"; OLLAMA_HOST=0.0.0.0 ollama serve &   # 默认只听 127.0.0.1，容器访问不到
```

> 安全提示：0.0.0.0 会把 Ollama 暴露到局域网，实验环境可接受；生产环境模型服务本来就该在集群内网里。

### 3. 部署进 kind 并验证（实测命令与结果）

```bash
kind load docker-image rag-service:v1 --name labs
kubectl apply -f manifests/rag.yaml
kubectl get pod -l app=rag        # 1/1 Running

# 从本机经 NodePort 调用集群内的 RAG 服务
curl -s "http://localhost:8080/query?q=容器被OOM杀掉的退出码是多少" | python3 -m json.tool
# 实测回答："根据参考资料，容器被OOM杀掉的退出码是137。" sources: k8s-notes.md
curl -s "http://localhost:8080/query?q=vLLM 为什么比原生推理快？" | python3 -c "import json,sys; print(json.load(sys.stdin)['answer'])"
# 实测回答列出 PagedAttention 与连续批处理两大机制，sources: llm-notes.md
```

### 4. Prometheus 自动发现（全链路闭环，实测）

```bash
kubectl port-forward deploy/prometheus 19091:9090 &
curl -s http://localhost:19091/api/v1/targets | python3 -m json.tool | grep -B 2 -A 4 rag
# 实测：rag-798c9c46c6-swps7 → "health": "up"（注解发现，零配置接入）
curl -s 'http://localhost:19091/api/v1/query?query=rag_requests_total'
# 实测：rag_requests_total = 1（和服务的 /metrics 一致）
```

在 Grafana（Lab 10 部署的）里把数据源指向 Prometheus 后，用 `rate(rag_requests_total[5m])` 画 QPS、`rate(rag_latency_ms_sum[5m]) / rate(rag_requests_total[5m])` 画平均延迟 —— **AI 服务监控面板的核心两条线**。

## 观察与思考

1. 容器里的向量库是内存态（chromadb.Client()），Pod 重启索引重建要几秒 —— 知识库大了怎么办？（挂 PVC 存持久化索引，或换独立向量库服务 —— 又回到 k8s-labs Lab 04 的存储知识）
2. 多副本会怎样？（RAG 服务无状态，直接扩副本；但本实验 hostNetwork 的 Pod 都占节点 8000 端口，**hostNetwork 多副本必冲突** —— 生产用普通 Pod 网络 + Service，这就是为什么真实集群不这么跑）
3. 0.5B 模型在 Lab 06 实测中回答要点正确但**表达重复啰嗦**（同一要点换三种说法各说一遍）—— 小模型的通病。呼应 Lab 04 的结论：**检索质量 ≠ 答案质量，生成端也要评估**；生产上靠更强模型、重复惩罚参数或生成后处理来治。

## 常见坑

- chromadb 集合名最少 3 个字符（`kb` 会报 Validation error，用 `rag_kb`，实测踩过）
- `ollama.chat()` 默认连 127.0.0.1 —— 容器里必须显式 `ollama.Client(host=OLLAMA_URL)`（实测踩过）
- python:3.12-slim 记得先从镜像站拉取再 build，否则 buildx 直连 docker.io 失败
- hostNetwork Pod 的 readiness 探针走的是节点端口，端口被占会一直 NotReady —— 排查看 `kubectl describe`
