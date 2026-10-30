# Lab 04 — Agentic RAG：会自己决定"何时检索、怎么检索"的 RAG

> **新版必做：[业务开发、生产故障与验收](BUSINESS-PRACTICE.md)**。原脚本是机制演示，旧“实测”仅指旧用例，不代表新增业务或生产就绪；以新版路线的边界和验收为准。

> **原示例边界校正：** 相似度低不代表可以改为凭模型常识回答客户事实。无合同/SLA或实时证据时必须明确缺失；exit 137本身也不足以单独认定OOM。历史样例不能推导通用模型性能。



## 📖 本章学习指导
> 建议时长 **3 小时** ｜ 前置：agent Lab01-02 + llmops Lab03 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q16

**学习循环：**
1. 读（25min）：三阶段决策（检索决策/查询改写/反思重查）的代码注释
2. 跑（40min）：三个默认问题——重点观察 ② "1+1 等于几"被决策为**不检索**（省成本）
3. 破坏练习（30min）：① 把 decide_need_retrieval 换成恒 true，对比多花的时延与 token；② 问一个知识库没有的问题，看反思重查与最终拒答
4. 验收自测：① pipeline RAG 与 agentic RAG 的本质区别？② 查询改写为什么常是最大增益？③ 何时"不检索"反而对？
5. 产出：一张"agentic RAG 决策流"手绘图

## 核心问答

**Q1：Agentic RAG 相比普通 RAG 的收益与代价？**

> 收益（实测）：① 该不查的就不查（"1+1"跳过检索）；② 查询改写把口语转术语（"容器被杀"→"container oom killed exit code"），检索命中率显著提高；③ 结果不好能换词重查。代价：每次提问多 1-2 次 LLM 调用（时延与成本）——所以生产上常用"小模型做决策+改写，大模型做最终回答"的分工。

**Q2：查询改写为什么常是 Agentic RAG 的最大增益来源？**

> 实测对比（以"容器被 OOM 杀掉的退出码"为例）：
> - **不改写直接查**：中文查询 → bge-m3 嵌入 → top-1 距离 0.612，检索到的块不含答案
> - **改写后查询**："container oom killed exit code" → top-1 距离 0.508，精准命中 k8s-notes.md 的 OOMKilled 段落
>
> 原因：嵌入模型对术语的向量空间对齐更好（英文术语在训练数据中更密集），改写相当于"把查询映射到文档的语义空间"。这是 Agentic RAG 最划算的一次 LLM 调用。

**Q3：何时"不检索"反而是正确决策？如何避免过度检索？**

> 三类场景不该检索：① 常识问题（"1+1"、"Python 是什么"）；② 上下文内已有答案（多轮对话中的追问）；③ 纯计算/推理任务（"帮我写个排序算法"）。
>
> 避免过度检索的工程手段：① 用小模型（0.5B）做 need_retrieval 二分类，成本极低；② 维护"高频无需检索问题"的缓存；③ 检索后评估相关性分数，低于阈值则丢弃检索结果直接用模型回答——实测本实验的三阶段决策（need→rewrite→reflect）已经把这三点都覆盖了。

## 实测记录
- "容器被 OOM 杀掉的退出码" → 改写为英文术语 → 命中 k8s-notes.md → **137** ✓
- "1+1 等于几？" → 决策 need=false → 跳过检索直接答 ✓
- "什么是 PagedAttention" → 改写为 "pagedattention" → 命中 → 正确定义 ✓

## 运行
```bash
cd ~/Documents/ai-labs/agent-labs/lab04-agentic-rag
LITELLM_LOCAL_MODEL_COST_MAP=True ~/Documents/ai-labs/llmops-labs/.venv/bin/python agentic_rag.py
```
