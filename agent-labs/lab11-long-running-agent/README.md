# Lab 11 — 长程 Agent：流式诊断、Checkpoint 恢复与成本守卫

> **Capstone 实验** | 建议时长 **10 小时** | 前置：Lab 01–10 全部  
> 一次性覆盖 Agent 开发的 **12 个重难点**，解决一个真实有价值的问题。

## 为什么需要这个实验

你的课程体系已经覆盖了 Agent 基础（ReAct循环、工具注册、记忆、RAG、多Agent、MCP、安全、部署、Workflow、审批），但有一个关键缺口：**所有实验都是同步、短时的**。

现实中，企业 Agent 面对的任务往往是：
- 一次网络故障诊断要跑 15–30 分钟，中间有多次工具调用、人工确认、等待
- 客户端需要实时看到诊断进度（"正在查询上海节点告警…"）
- 进程崩了、网络断了，恢复后不能从头再来
- 每次诊断有 Token 预算上限，超了要优雅降级
- 多个诊断子任务要并行执行，而不是串行排队

**业界怎么做的？**

| 方案 | 代表 | 核心思想 | 适用场景 |
|------|------|---------|---------|
| **Durable Execution** | Temporal, Inngest, Restate | 框架自动在每一步做 checkpoint，崩溃后从最后成功步骤恢复 | 多步骤 Workflow（小时~天级） |
| **Event Sourcing** | Temporal Event History | 记录每一步的输入输出，重放时只跑逻辑不重跑工具 | 审计、调试、可复现 |
| **Memory Hierarchy** | LangGraph Memory Store | 短期=上下文窗口，长期=向量库/KV，按相关性注入 | 长对话、跨会话 |
| **Streaming (SSE)** | OpenAI Streaming API | Token 级流式输出，客户端实时显示 | 用户体验 |
| **Checkpoint + 人工门** | LangGraph Checkpoint | 在关键节点存盘，等待人工 Signal 后继续 | 高风险操作 |
| **Cost Guard** | Anthropic Best Practice | 每次请求有 Token 预算，累计超限时降级或终止 | 成本控制 |

本实验把以上模式**全部整合到一个 Agent 里**。

---

## 业务场景：网络故障自主诊断 Agent

**问题**：云网络运维工程师每天收到大量故障工单（"上海到香港延迟升高"、"某客户 VPN 断开"），大部分需要 5–8 步排查，耗时 15–30 分钟。80% 的故障原因是重复的（光衰、BGP 抖动、配置错误），但每次都要人工逐条查工具、翻手册、写报告。

**Agent 做什么**：
1. 接收故障工单（电路ID + 现象描述）
2. 自主执行多轮诊断（查电路状态、查告警、查手册、查历史工单）
3. 并行执行多个独立的检查子任务
4. 实时通过 SSE 流式推送诊断进度给前端
5. 在关键节点（如判定根因、生成建议）等待人工确认
6. 支持进程崩溃后从最后的 checkpoint 恢复
7. 有 Token 预算守卫，超限时降级到摘要模式
8. 输出结构化诊断报告（含证据链、置信度、建议动作）

**为什么这个问题有价值？**
- 每次诊断节省 10–20 分钟 × 每天 20+ 工单 = 每天节省 3–7 小时人力
- 诊断质量标准化，不再依赖个人经验
- 诊断过程可追溯、可复盘

---

## 覆盖的 12 个重难点

| # | 知识点 | 本实验中的体现 | 对应前序 Lab |
|---|--------|---------------|-------------|
| 1 | **ReAct 循环 + 规划** | 多轮诊断决策：观察→假设→验证→结论 | Lab 01, 05 |
| 2 | **工具注册 + JSON Schema** | 8 个诊断工具的注册、参数校验、租户授权 | Lab 02 |
| 3 | **短期记忆压缩** | 诊断到第 10 轮时，前 6 轮自动压缩成纪要 | Lab 03 |
| 4 | **长期记忆 + RAG** | 历史故障模式库检索、运维手册检索 | Lab 03, 04 |
| 5 | **多 Agent 并行** | 电路检查、告警分析、手册检索三个子 Agent 并行执行 | Lab 05 |
| 6 | **MCP 协议** | 将监控工具封装为 MCP Server，支持版本协商 | Lab 06 |
| 7 | **安全与护栏** | 工具白名单、参数范围校验、输出过滤（不泄露内部 IP） | Lab 07 |
| 8 | **生产部署** | FastAPI HTTP 接口 + SSE 端点 + Prometheus 指标 | Lab 08 |
| 9 | **Workflow vs Agent** | 诊断流程是 Agent（模型决策）；报告生成是 Workflow（确定性） | Lab 09 |
| 10 | **人工审批 + 持久化** | 诊断报告需人工确认后才归档；SQLite checkpoint | Lab 10 |
| 11 | **SSE 流式推送** ⭐新 | 客户端实时接收诊断事件（thinking/tool_call/finding/conclusion） | 本实验新增 |
| 12 | **成本守卫 + 模型路由** ⭐新 | 每次诊断有 Token 预算；简单检查用小模型，根因分析用大模型 | 本实验新增 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      客户端（前端）                       │
│   EventSource → 实时显示诊断进度、发现、结论              │
└──────────────────────┬──────────────────────────────────┘
                       │ SSE (text/event-stream)
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI 网关层                           │
│  POST /api/v1/diagnose  → 创建诊断任务，返回 task_id     │
│  GET  /api/v1/diagnose/{id}/stream → SSE 流              │
│  POST /api/v1/diagnose/{id}/confirm → 人工确认           │
│  GET  /api/v1/diagnose/{id}/status → 当前状态            │
├─────────────────────────────────────────────────────────┤
│                  成本守卫 (CostGuard)                     │
│  每次诊断: budget=50K tokens                             │
│  累计追踪: input_tokens + output_tokens                  │
│  超 80%: 降级到摘要模式（压缩历史、跳过可选步骤）         │
│  超 100%: 终止诊断，输出已有发现 + "预算耗尽"             │
├─────────────────────────────────────────────────────────┤
│                  诊断引擎 (DiagnosisEngine)               │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              模型路由 (ModelRouter)                │   │
│  │  简单分类/格式转换 → qwen-small (便宜)            │   │
│  │  工具选择/参数生成 → qwen-medium (平衡)           │   │
│  │  根因推理/报告生成 → qwen-strong (精准)           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │          诊断循环 (DiagnosisLoop)                  │   │
│  │                                                  │   │
│  │  for step in range(max_steps):                   │   │
│  │    1. checkpoint()          # SQLite 存盘         │   │
│  │    2. context = memory.build()  # 短期+长期      │   │
│  │    3. decision = llm.route(context)  # 模型路由   │   │
│  │    4. emit_event(SSE, decision)  # 流式推送      │   │
│  │    5. if needs_parallel:                         │   │
│  │         results = asyncio.gather(                │   │
│  │           sub_agent_1(), sub_agent_2(), ...      │   │
│  │         )                                        │   │
│  │       else:                                      │   │
│  │         result = tool_registry.execute(decision) │   │
│  │    6. memory.add(result)     # 更新记忆          │   │
│  │    7. cost_guard.track(tokens)  # 成本追踪       │   │
│  │    8. if is_human_gate:                          │   │
│  │         emit_event(SSE, "awaiting_confirm")      │   │
│  │         await approval_signal()  # 阻塞等人工    │   │
│  │    9. memory.maybe_compress() # 短期记忆压缩     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              工具注册表 (ToolRegistry)             │   │
│  │  @tool get_circuit(circuit_id, tenant_id)        │   │
│  │  @tool list_alerts(circuit_id, start, end)       │   │
│  │  @tool search_runbook(query)           # RAG     │   │
│  │  @tool get_job_status(job_id)                    │   │
│  │  @tool check_bgp_neighbor(device_id)             │   │
│  │  @tool get_historical_incidents(pattern)  # RAG  │   │
│  │  @tool measure_latency(src, dst, count)          │   │
│  │  @tool get_port_status(device_id, port)          │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                  持久化层 (SQLite)                        │
│  diagnosis_tasks: id, tenant_id, circuit_id, status,    │
│                   checkpoint_json, step_count,          │
│                   token_usage, created_at, updated_at   │
│  diagnosis_steps: task_id, step_num, action,           │
│                   tool_name, tool_args, tool_result,    │
│                   tokens_used, timestamp                │
│  diagnosis_findings: task_id, finding_type, content,   │
│                   confidence, evidence_refs             │
│  approvals: task_id, proposal_hash, actor, decision,   │
│             expires_at                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 实现里程碑（5 个阶段）

### 阶段 1：诊断工具层 + 基础循环（2 小时）

**目标**：8 个诊断工具注册完毕，基础 ReAct 循环跑通一个最简单的故障场景。

**手写项**：
1. `ToolRegistry` 复用 Lab 02 的注册表，新增 **租户授权**：每个工具调用前检查 `tenant_id` 是否有权访问该电路
2. 8 个诊断工具的 JSON Schema + FakeBackend（返回 fixture 数据）
3. `DiagnosisLoop`：基础 ReAct 循环，最大 12 步
4. `Fixture 数据`：至少 3 个故障场景的完整数据

**故障场景（必须手写 fixture）**：

| 场景 | 现象 | 根因 | 诊断步骤数 |
|------|------|------|-----------|
| 光衰故障 | 上海-香港延迟升高 | 光纤衰减超阈值 | 5 步 |
| BGP 抖动 | VPN 间歇断开 | BGP 邻居 flap | 7 步 |
| 配置错误 | 新电路不通 | VLAN 未放行 | 4 步 |

**验收**：给定光衰场景的 fixture，Agent 在 6 步内正确定位"光纤衰减"并输出诊断报告。

---

### 阶段 2：记忆 + RAG + 并行诊断（2 小时）

**目标**：长对话不丢失上下文；多子任务并行执行；能从知识库检索历史案例。

**手写项**：
1. `DiagnosisMemory`：
   - 短期：对话历史 + 超过 6 轮触发压缩（旧轮次→LLM摘要→"诊断纪要"）
   - 长期：历史故障模式库（SQLite FTS5 全文检索），每轮注入相关历史案例
   - 压缩策略：保留 system + 最近 3 轮原文 + 纪要 + 关键发现列表
2. `ParallelDiagnosis`：
   - 当诊断到"需要多角度检查"时，同时启动 3 个子任务：
     - 电路状态检查（get_circuit + get_port_status）
     - 告警分析（list_alerts + 严重性判定）
     - 知识检索（search_runbook + get_historical_incidents）
   - 使用 `asyncio.gather()` 并行执行，合并结果后继续推理
3. `HistoricalIncidentStore`：
   - 至少 10 条历史故障记录（pattern、root_cause、resolution、confidence）
   - 检索接口：按关键词 + 电路类型匹配，返回 Top 3 相关案例

**验收**：
- 诊断到第 8 轮时，前 5 轮已被压缩成纪要，但关键发现（"光衰 -12dBm"）未丢失
- 并行执行 3 个子任务，总耗时 < 单个子任务的 2 倍（而非 3 倍）
- 检索到"2024-03 京沪干线光衰"历史案例，并引用在报告中

---

### 阶段 3：SSE 流式推送 + 模型路由（2 小时）

**目标**：客户端实时看到诊断进度；不同复杂度的决策用不同模型。

**手写项**：
1. `SSE Stream`：
   - FastAPI 端点 `GET /diagnose/{id}/stream`，返回 `text/event-stream`
   - 事件类型：
     ```
     event: thinking
     data: {"step": 3, "content": "分析告警数据，发现光功率异常..."}

     event: tool_call
     data: {"step": 3, "tool": "list_alerts", "args": {"circuit_id": "CKT-001"}}

     event: tool_result
     data: {"step": 3, "tool": "list_alerts", "result_summary": "发现 3 条 LOS 告警"}

     event: finding
     data: {"step": 4, "type": "evidence", "content": "光功率 -12dBm，低于阈值 -8dBm"}

     event: parallel_start
     data: {"step": 5, "agents": ["circuit_check", "alarm_analysis", "knowledge_search"]}

     event: parallel_complete
     data: {"step": 5, "results_count": 3}

     event: awaiting_confirm
     data: {"step": 8, "question": "是否判定根因为光纤衰减？", "confidence": 0.85}

     event: conclusion
     data: {"step": 10, "root_cause": "光纤衰减", "confidence": 0.92}

     event: done
     data: {"total_steps": 10, "total_tokens": 28500, "duration_seconds": 340}
     ```
   - 客户端重连时，从最后的 checkpoint 恢复流（用 `Last-Event-ID`）
2. `ModelRouter`：
   - 三级路由：
     - **轻量级**（qwen-small）：参数格式转换、简单分类（"这个告警是否严重？"）
     - **中等级**（qwen-medium）：工具选择、参数生成、证据关联
     - **重量级**（qwen-strong）：根因推理、诊断报告生成、不确定性判断
   - 路由规则：根据当前步骤类型自动选择，不由模型自己决定
   - Token 消耗记录：每次调用记录 model、input_tokens、output_tokens、cost_estimate

**验收**：
- 浏览器打开 SSE 端点，实时看到 10 个诊断步骤的事件流
- 模型路由日志显示：步骤 1-3 用 medium，步骤 8 的根因推理用 strong
- 断开 SSE 连接后重连，从断点继续接收后续事件

---

### 阶段 4：Checkpoint 恢复 + 成本守卫（2 小时）

**目标**：进程崩溃后从最后的 checkpoint 恢复；Token 超限时自动降级。

**手写项**：
1. `CheckpointManager`：
   - 每完成一步，将完整状态写入 SQLite：
     ```python
     checkpoint = {
         "task_id": "diag-001",
         "step": 5,
         "status": "investigating",     # investigating/awaiting_confirm/completed/failed
         "memory": {
             "summary": "前 3 轮纪要...",
             "recent_rounds": [...],     # 最近 3 轮原文
             "findings": [...],          # 已确认的发现列表
             "long_term_injections": [...]  # 已注入的长期记忆
         },
         "tool_results": {              # 已完成的工具调用结果（不重跑）
             "get_circuit_CKT001": {...},
             "list_alerts_CKT001": {...}
         },
         "pending_parallel": null,       # 如果崩溃时有未完成的并行任务
         "token_usage": {"input": 18000, "output": 5200, "cost_estimate": 0.034},
         "cost_budget": 50000,           # 总预算
         "created_at": "...",
         "updated_at": "..."
     }
     ```
   - 恢复逻辑：
     ```
     读取 checkpoint → 重建 memory → 跳过已完成的 tool_results → 从 step+1 继续
     ```
   - **关键约束**：已完成的工具调用不重跑（幂等性保证），只重跑模型推理
2. `CostGuard`：
   - 构造函数接收 `budget_tokens`（默认 50000）
   - 每次 LLM 调用后累加 `input_tokens + output_tokens`
   - 阈值行为：
     - **60%**：发出 warning 事件，记录日志
     - **80%**：进入降级模式——压缩历史更激进（保留 1 轮而非 3 轮）、跳过可选的深入检查步骤、后续推理全部用 medium 模型
     - **100%**：终止诊断，输出 `budget_exhausted` 事件，生成已有发现的 partial report
   - 降级事件必须通过 SSE 通知客户端

**验收**：
- 在第 5 步注入 crash（kill 进程），重启后从第 6 步继续，前 5 步的工具结果不重新调用
- 设置 budget=10000 tokens，诊断在第 4 步触发 80% 降级，第 6 步触发 100% 终止
- 降级后诊断报告标注 `"degraded": true, "degradation_reason": "cost_budget_80%"`

---

### 阶段 5：人工确认 + 输出过滤 + 端到端集成（2 小时）

**目标**：关键节点等待人工确认；输出过滤敏感信息；完整端到端跑通。

**手写项**：
1. `HumanGate`：
   - 在两个节点插入人工门：
     - **根因判定**：Agent 提出根因假设后，等待人工确认"同意/拒绝/修改"
     - **报告归档**：诊断报告生成后，等待人工确认后才标记 completed
   - 实现：checkpoint 状态设为 `awaiting_confirm`，SSE 发出 `awaiting_confirm` 事件，阻塞等待 `POST /diagnose/{id}/confirm` 请求
   - 超时机制：30 分钟无确认 → 自动标记 `expired`，输出 partial report
   - 审批绑定：和 Lab 10 一样，用 `proposal_hash` 确保确认的是当前内容
2. `OutputFilter`：
   - 诊断报告输出前过一遍过滤器：
     - **内部 IP 脱敏**：`10.x.x.x`、`192.168.x.x` → `10.x.x.*`
     - **设备密码/密钥**：正则检测并替换为 `[REDACTED]`
     - **客户名称**：根据租户配置决定是否展示全称或脱敏
   - 过滤器可配置（per-tenant 策略）
3. **端到端集成测试**：
   - 完整跑通光衰故障场景：
     1. `POST /diagnose` 创建任务 → 返回 task_id
     2. `GET /diagnose/{id}/stream` 连接 SSE → 实时接收事件
     3. Agent 执行 8 步诊断 → 每步都有 SSE 事件
     4. 第 8 步触发 `awaiting_confirm` → 等待人工确认
     5. `POST /diagnose/{id}/confirm` 确认根因 → Agent 继续
     6. 生成诊断报告 → 输出过滤 → SSE 推送 `done` 事件
     7. 在第 5 步注入 crash → 重启后从第 6 步继续
     8. 设置极低 budget → 触发降级 → 验证 partial report

**验收**：
- 端到端跑通，诊断报告包含：根因、证据链（至少 3 条）、置信度、建议动作
- 输出中无内部 IP 明文
- 崩溃恢复后诊断报告与不崩溃的报告一致（工具结果复用）
- 降级模式下报告标注降级原因

---

## 关键代码结构（参考骨架）

```python
# diagnosis_engine.py — 核心引擎骨架

import asyncio
import json
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator

class DiagnosisStatus(Enum):
    QUEUED = "queued"
    INVESTIGATING = "investigating"
    AWAITING_CONFIRM = "awaiting_confirm"
    COMPLETED = "completed"
    FAILED = "failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    EXPIRED = "expired"

class ModelTier(Enum):
    LIGHT = "qwen-small"      # 简单分类、格式转换
    MEDIUM = "qwen-medium"    # 工具选择、证据关联
    HEAVY = "qwen-strong"     # 根因推理、报告生成

@dataclass
class DiagnosisEvent:
    """SSE 事件：每次状态变化都推送给客户端"""
    event_type: str           # thinking/tool_call/tool_result/finding/...
    step: int
    data: dict
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class CostState:
    """成本追踪：每次 LLM 调用后更新"""
    budget: int = 50000       # Token 预算上限
    used_input: int = 0
    used_output: int = 0

    @property
    def usage_pct(self) -> float:
        return (self.used_input + self.used_output) / self.budget

    @property
    def is_degraded(self) -> bool:
        return self.usage_pct >= 0.8

    @property
    def is_exhausted(self) -> bool:
        return self.usage_pct >= 1.0

    def track(self, input_tokens: int, output_tokens: int):
        self.used_input += input_tokens
        self.used_output += output_tokens


class DiagnosisEngine:
    """长程诊断引擎：整合所有 Agent 知识点"""

    def __init__(self, task_id: str, tenant_id: str, circuit_id: str,
                 tool_registry, memory, model_router, checkpoint_mgr,
                 cost_guard: CostState, output_filter):
        self.task_id = task_id
        self.tenant_id = tenant_id
        self.circuit_id = circuit_id
        self.tools = tool_registry
        self.memory = memory
        self.router = model_router
        self.checkpoint = checkpoint_mgr
        self.cost = cost_guard
        self.filter = output_filter
        self.findings: list[dict] = []
        self.events: asyncio.Queue[DiagnosisEvent] = asyncio.Queue()

    async def run(self) -> AsyncIterator[DiagnosisEvent]:
        """主诊断循环：每步 checkpoint + 流式推送 + 成本守卫"""
        # 尝试从 checkpoint 恢复
        state = self.checkpoint.load(self.task_id)
        start_step = state["step"] + 1 if state else 1

        for step in range(start_step, max_steps := 12):
            # 1. 成本检查
            if self.cost.is_exhausted:
                yield self._emit("budget_exhausted", step, {
                    "reason": "token_budget_exceeded",
                    "used": self.cost.used_input + self.cost.used_output
                })
                return

            # 2. 构建上下文（短期记忆 + 长期记忆注入）
            context = self.memory.build_messages()

            # 3. 模型路由：根据步骤类型选模型
            tier = self._route_model(step, context)

            # 4. 决策
            yield self._emit("thinking", step, {"tier": tier.value})
            decision = await self._call_llm(context, tier)

            # 5. 执行（支持并行）
            if decision.get("parallel"):
                yield self._emit("parallel_start", step, decision["parallel"])
                results = await asyncio.gather(
                    *[self._execute_sub_task(t) for t in decision["parallel"]]
                )
                yield self._emit("parallel_complete", step, {"count": len(results)})
            else:
                result = await self._execute_tool(decision)
                yield self._emit("tool_result", step, result)

            # 6. 更新记忆 + 成本追踪
            self.memory.add(decision, result if not decision.get("parallel") else results)
            self.cost.track(decision.get("tokens_in", 0), decision.get("tokens_out", 0))

            # 7. 短期记忆压缩
            if self.cost.is_degraded:
                self.memory.compress_aggressive()  # 降级：只留 1 轮
            else:
                self.memory.maybe_compress()

            # 8. Checkpoint
            self.checkpoint.save(self.task_id, step, self._snapshot())

            # 9. 人工门
            if decision.get("needs_confirm"):
                yield self._emit("awaiting_confirm", step, decision["proposal"])
                self.checkpoint.save_status(self.task_id, "awaiting_confirm")
                confirmed = await self._wait_for_confirmation()
                if not confirmed:
                    yield self._emit("expired", step, {})
                    return

            # 10. 结论判定
            if decision.get("action") == "conclusion":
                report = self._build_report()
                filtered_report = self.filter.apply(report)
                yield self._emit("conclusion", step, filtered_report)
                yield self._emit("done", step, {
                    "total_steps": step,
                    "total_tokens": self.cost.used_input + self.cost.used_output,
                })
                return

    def _route_model(self, step: int, context: list) -> ModelTier:
        """模型路由：不是让模型选，而是代码逻辑决定"""
        if step <= 2:
            return ModelTier.MEDIUM       # 初始探索
        if step >= 8:
            return ModelTier.HEAVY        # 根因推理
        return ModelTier.MEDIUM           # 中间步骤

    def _emit(self, event_type: str, step: int, data: dict) -> DiagnosisEvent:
        return DiagnosisEvent(event_type=event_type, step=step, data=data)
```

---

## 与前序 Lab 的关系图

```
Lab 01 (ReAct循环) ──────────────────────────┐
Lab 02 (工具注册+Schema) ────────────────────┤
Lab 03 (记忆压缩+长期记忆) ──────────────────┤
Lab 04 (RAG检索) ────────────────────────────┤
Lab 05 (多Agent并行) ────────────────────────┤
Lab 06 (MCP协议) ────────────────────────────┼──→ Lab 11 (长程诊断Agent)
Lab 07 (安全护栏+输出过滤) ──────────────────┤       = Capstone 整合实验
Lab 08 (HTTP API+Prometheus) ────────────────┤
Lab 09 (确定性Workflow) ─────────────────────┤
Lab 10 (Checkpoint+审批) ────────────────────┘
                                              +
                                              新增: SSE 流式推送
                                              新增: 模型路由+成本守卫
                                              新增: asyncio 并行
```

---

## 面试金句（本实验产出的核心论点）

> **"企业级长程 Agent 的核心不是让模型更聪明，而是让基础设施替模型记住一切。"**

> **"Temporal/Inngest 的 durable execution 本质是：把 Agent 的每一步决策和工具结果都存盘，崩溃后从最后的成功步骤继续，而不是从头再来。这和我们 Lab 10 的 checkpoint 是同一个思想，只是框架帮你做了。"**

> **"成本守卫不是可选项——没有 Token 预算的 Agent 就是一个无限烧钱的循环。80% 降级、100% 终止、全程追踪，这是生产 Agent 的底线。"**

> **"SSE 流式推送不是锦上添花，而是长程 Agent 的必需品——用户不会盯着一个转了 15 分钟的 loading 不动。每一步的 thinking、tool_call、finding 都要实时推给前端。"**

> **"模型路由是成本优化的核心杠杆：80% 的决策用 medium 模型就够了，只在根因推理和报告生成时才需要 strong 模型。这一个改变就能省 60% 的 Token 费用。"**

---

## 运行

```bash
cd ~/Documents/ai-labs/agent-labs/lab11-long-running-agent

# 安装依赖（asyncio, fastapi, sse-starlette）
pip install fastapi sse-starlette uvicorn

# 运行诊断服务
LITELLM_LOCAL_MODEL_COST_MAP=True python diagnosis_server.py

# 客户端测试（curl SSE 流）
curl -N http://localhost:8000/api/v1/diagnose/diag-001/stream

# 创建诊断任务
curl -X POST http://localhost:8000/api/v1/diagnose \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "T001", "circuit_id": "CKT-001", "symptom": "上海到香港延迟升高"}'

# 人工确认
curl -X POST http://localhost:8000/api/v1/diagnose/diag-001/confirm \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "actor": "ops-admin", "proposal_hash": "sha256:..."}'

# 运行测试
python -m pytest tests/ -v
```

---

## 验收标准

| 维度 | 通过条件 |
|------|---------|
| 功能正确 | 3 个故障场景全部正确诊断，报告含证据链 |
| 长程可靠 | 在第 5 步 crash → 恢复后诊断结果一致，工具不重跑 |
| 流式实时 | SSE 事件延迟 < 1 秒，客户端断线重连后继续 |
| 成本可控 | budget=10K 时正确降级，budget=5K 时正确终止 |
| 安全合规 | 输出中无内部 IP 明文，越权查询被拒绝 |
| 人工门 | 未经确认不归档，审批过期不执行，内容变更需重审 |
| 并行有效 | 3 个子任务并行总耗时 < 串行的 70% |

---

## 扩展方向（可选）

1. **接入真实 MCP Server**：将 Lab 06 的 MCP 工具作为诊断工具接入
2. **接入 Lab 09 周报**：诊断结果自动汇总到安全周报
3. **接入 Temporal**：用 Temporal 替代自建 checkpoint，对比复杂度和可靠性
4. **前端 UI**：用 React + EventSource 构建实时诊断看板
5. **Grafana 仪表盘**：Prometheus 指标可视化（诊断次数、平均步骤、Token 消耗、降级率）
