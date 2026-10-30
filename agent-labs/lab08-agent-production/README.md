# Lab 08 — 毕业项目：Agent 服务生产化（HTTP + K8s + 指标）

> **新版必做：[业务开发、生产故障与验收](BUSINESS-PRACTICE.md)**。原脚本是机制演示，旧“实测”仅指旧用例，不代表新增业务或生产就绪；以新版路线的边界和验收为准。

> **原示例边界校正：** 当前实际代码只有GET /run(task)，并没有暴露max_steps参数、认证、持久化或真正的总超时；因此下文相关设计描述是目标而非已有功能。累计时延sum不能直接计算P95，且工具调用数不等于思考深度。hostNetwork与NodePort是本地演示选择，非通用生产架构；建议使用port-forward验证，kind默认未映射30081。



## 📖 本章学习指导
> 建议时长 **3 小时** ｜ 前置：agent Lab01-07 + k8s-labs Lab07/10 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q1/Q3

**学习循环：**
1. 读（20min）：agent_service.py 与 llmops-labs/lab06 的同构性（同一套生产化模板）
2. 跑（40min）：本地 uvicorn 冒烟（/run + /metrics）→ 构建镜像 → 部署 kind → NodePort 30081 验证 → Prometheus target up
3. 破坏练习（30min）：① 把 manifests 的 nodePort 改成 30080（撞 RAG 服务端口）复现 k8s-labs Lab07 的冲突课；② MODEL 换 qwen-small vs qwen-strong 对比步数
4. 验收自测：① Agent 服务的三个 SLI（请求数/工具调用数/时延）？② 步数限制为什么是接口级安全参数？③ 和 RAG 服务共用什么生产模式？
5. **产出**：Agent 服务在 K8s 运行 + Prometheus 抓到 agent_tool_calls_total 的截图——**你与其他候选人拉开差距的实物证据**

## 核心问答

**Q1：Agent 服务化的三个 SLI（Service Level Indicator）是什么？为什么选这三个？**

> 三个 SLI：
> 1. **请求数（agent_requests_total）**：业务量指标，用于容量规划和计费
> 2. **工具调用数（agent_tool_calls_total）**：复杂度指标，反映 Agent 的"思考深度"——单次请求调用 3 次工具 vs 10 次工具，成本和延迟差异巨大
> 3. **时延（agent_duration_seconds）**：用户体验指标，Agent 的端到端延迟（包括多轮 LLM 调用 + 工具执行）
>
> 为什么选这三个？因为它们覆盖了**业务价值（请求数）+ 成本（工具调用数）+ 体验（时延）**三个维度。只监控请求数会漏掉"单次请求调用 50 次工具烧掉 $1"的异常；只监控时延会漏掉"Agent 在死循环但还没超时"的问题。

**Q2：步数限制（max_steps）为什么是接口级安全参数，而不是配置项？**

> 因为**恶意用户可以通过构造复杂任务触发 Agent 无限循环**，消耗大量 LLM tokens 和工具调用资源。
>
> 如果 max_steps 是全局配置（如 `MAX_STEPS=10`），攻击者可以提交 100 个并发请求，每个请求都跑满 10 步 → 瞬间消耗 1000 次工具调用。
>
> 把 max_steps 暴露为接口参数（`/run?task=...&max_steps=5`）的好处：
> 1. **调用方自控成本**：简单任务传 max_steps=3，复杂任务传 max_steps=10
> 2. **网关层限流**：可以对单个 API key 限制 max_steps 的上限（如免费用户最多 5 步）
> 3. **防御性默认值**：服务端设置默认 max_steps=3，调用方不传就用保守值
>
> 这是"安全参数外置"的设计模式——和数据库的 `query_timeout`、HTTP 的 `timeout` 是同一个思路。

**Q3：本实验的 Agent 服务和 llmops-labs 的 RAG 服务共用什么生产模式？**

> 两者完全同构，共用同一套"AI 服务生产化模板"：
>
> | 维度 | RAG 服务（llmops-lab06） | Agent 服务（本实验） |
> |------|------------------------|---------------------|
> | 框架 | FastAPI | FastAPI |
> | 核心接口 | `/query?q=...` | `/run?task=...` |
> | 指标接口 | `/metrics` | `/metrics` |
> | 指标名 | `rag_requests_total` | `agent_requests_total` |
> | K8s 部署 | hostNetwork + NodePort | hostNetwork + NodePort |
> | 监控 | Prometheus 注解发现 | Prometheus 注解发现 |
>
> 这种同构性不是巧合——**所有 AI 服务的生产化都是同一套模式**：HTTP API + Prometheus 指标 + K8s 部署 + 注解发现。掌握这个模板后，新增一个 AI 服务（如 Embedding 服务、Classifier 服务）只需要替换核心业务逻辑，生产化部分直接复用。
>
> 数据工程师的类比：这和"所有 ETL 任务都走同一个 Airflow DAG 模板"是同一个思想——标准化降低运维成本。

## 实测记录（本地冒烟）
`/run?task=算一下 99 乘以 101` → 回答 **9999**，3 步，agent_tool_calls_total=1 ✓；K8s 部署模式与 RAG 服务（已验证）完全同构。

## 运行
```bash
cd ~/Documents/ai-labs/agent-labs/lab08-agent-production
~/Documents/ai-labs/llmops-labs/.venv/bin/uvicorn agent_service:app --port 18002   # 本地
# K8s：构建镜像 → kind load → kubectl apply -f manifests/agent.yaml
```
