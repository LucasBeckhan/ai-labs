# Lab 08 — GPU 推理生产化（原理篇）：vLLM、显存、GPU 调度

> 📖 本实验为原理篇：本机无 GPU，无法实操；内容为 GPU 推理生产化的核心原理与容量规划方法，配本机可跑的对照实验。

## 📖 本章学习指导

> 建议时长 **2.5 小时（原理+对照实验）** ｜ 前置：K8s Lab 06 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q2-Q3

**学习循环：**
1. **读**（40min）：本篇是原理篇——PagedAttention/连续批处理/显存估算三块逐段读透
2. **跑**（40min）：**必做两个本机对照实验**（吞吐对照/上下文成本）+ 手算三个模型规格的显存表
3. **验收自测**：① vLLM 两大机制？② 7B FP16 显存估算（现场算）？③ GPU 调度三件套（device plugin/污点/时间切片）？
4. **产出**：你手算的显存估算表（拍照存档——面试现场算题的底气）

## 学习目标

- 讲清 **vLLM 为什么快**：PagedAttention 与连续批处理（continuous batching）
- 会做**显存估算**（AI Infra 方向的核心硬技能）
- 把 k8s-labs Lab 06 的 GPU 调度知识和推理服务串联成完整的生产拓扑

## 核心问答

**Q1：vLLM 为什么比原生 transformers 推理快一个数量级？**

> 参考答法：两大机制。① **PagedAttention**：把 KV Cache 像操作系统内存分页一样按块管理 —— 传统实现按"最大长度"预分配连续显存，碎片率高达 60~80%；分页后显存利用率接近满载，同等显存能塞下几倍的并发。② **连续批处理（continuous batching）**：传统静态批要等整批都生成完才接新请求；连续批让新请求在任意 decode 步骤插队、已完成的立即退出 —— GPU 始终满负荷。一句话：**把操作系统的虚拟内存和调度思想用在 KV Cache 上**（这也是为什么它叫 "LLM 推理的操作系统"）。

**Q2：估算：一个 7B 模型（FP16），A10 24GB 显卡，最多能同时服务多少并发？**

> 参考答法（给方法，不是背数）：权重 7B×2B=14GB；剩 ~10GB 给 KV Cache。KV Cache 每 token = 2(K/V) × 层数 × 隐藏维度 × 2B ≈ 2×32×4096×2 ≈ 512KB/token（7B 模型量级）。假设每请求平均驻留 2000 token → 每请求 ~1GB → 理论 10 路并发；PagedAttention 后利用率接近满载、并发再乘几倍。**先报公式再带假设 —— 重点是展示估算方法，而不是背数字**。

**Q3：GPU 资源在 K8s 上怎么管？**

> 参考答法（全部在 k8s-labs 有落点）：① 节点装 NVIDIA device plugin 后 GPU 成为扩展资源，Pod 用 `resources.limits: nvidia.com/gpu: 1` 申请（Lab 06 调度）；② GPU 节点打污点防普通任务抢占（Lab 06）；③ 整卡太浪费时用 **time-slicing** 共享（隔离弱，适合推理副本）或 MIG 硬隔离（适合多租户）；④ 新方向：DRA（Dynamic Resource Allocation）按需分配。再往上：KServe/Kueue 管推理服务生命周期和训练队列。

## 与你已有实验的衔接（生产拓扑终图）

```
应用 → LiteLLM 网关(多模型路由/预算, Lab 02) → vLLM Deployment(GPU 节点池, 污点+device plugin, Lab 06)
                                                  ├─ HPA: 自定义指标(TTFT/token吞吐, Lab 09 思想)
                                                  └─ Prometheus: 延迟/显存/队列深度(本仓库 Lab 06)
RAG 应用(本仓库 Lab 06) → 网关 → 模型；评估流水线(Lab 04)管住每次模型/参数变更
```

## 本机可跑的对照实验（无 GPU 也能做）

1. **观察批处理的收益**（本机实测）：Lab 01 的 Ollama，同一问题跑 10 次，串行 5.9s / 85.4 tok/s，并发 8 路 3.8s / 94.5 tok/s —— **墙钟时间提升 1.52x**。CPU 推理收益温和（batch 能力有限），GPU + vLLM 的连续批处理会把倍数拉大一个量级 —— 这正是推理引擎优化的空间所在。
2. **观察 KV Cache 的代价**：同一问题分别带 100 字和 8000 字的上下文，对比 prompt_tokens 与响应时间 —— 上下文越长、prefill 越贵，这就是"长上下文成本"的体感，也是 RAG 要控制检索条数（Lab 04 TOP_K）的推理侧原因。
3. **显存估算练习**：用上面的公式给 Qwen2.5-7B / 14B / 32B 各算一遍 FP16 和 Q4 的权重显存 + 2000 token 并发的 KV Cache —— 算出来的表就是你做容量规划时的第一手参考。

## 延伸（做完上面的再看）

- vLLM 的 PagedAttention 论文（v1）+ v2 的 prefix caching：缓存公共前缀的 KV（RAG 场景 system prompt 不变 → 直接省钱省时间，和 Lab 03 的固定模板对上了）
- SGLang 的 RadixAttention：前缀树管理 KV，效果同理
- 推理服务的指标体系：TTFT、TPOT、吞吐、队列深度 —— 对应 Lab 06 /metrics 的进阶版

## 验证说明（透明）

本机无 GPU：标注"估算/对照"的部分已在本机验证思路可跑（对照实验 1、2 用 CPU 推理完成），GPU 特有行为（device plugin、time-slicing、显存行为）为原理讲解 + k8s-labs Lab 06 已验证的调度机制，未做真机验证。
