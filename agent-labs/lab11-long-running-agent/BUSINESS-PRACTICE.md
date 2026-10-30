# Lab 11 业务练习：长程诊断 Agent 的端到端交付

> 建议 6 小时。README 是机制骨架，本页是业务必做。完成后提交 work/ 代码、测试和复盘。

## 业务输入与完成边界

运营工程师收到故障工单后，系统自动创建诊断任务。Agent 必须在租户授权范围内执行诊断，不能越权查看其他租户电路。诊断过程中前端需要实时看到进度。进程崩溃后必须恢复。每次诊断有 Token 成本上限。诊断报告需人工确认后才归档。

先回答：谁发起诊断？允许查哪些电路和告警？哪些判定需要人工确认？崩溃恢复后哪些步骤不能重跑？Token 花完了怎么结束？这五项写入 work/DESIGN.md 后再编码。

## 从空白手写的任务

### 1. 诊断工具层（60 分钟）

手写 8 个诊断工具的完整 JSON Schema，每个工具必须包含：
- 参数名、类型、description、枚举值范围
- required 列表
- 租户授权检查（tenant_id 必须匹配电路归属）

```python
# 必须实现的工具签名
@registry.tool(description="查询电路状态，含光功率和端口状态")
def get_circuit(circuit_id: str, tenant_id: str) -> dict:
    ...

@registry.tool(description="查询指定电路在时间窗口内的告警列表")
def list_alerts(circuit_id: str, tenant_id: str, start: str, end: str) -> dict:
    ...

@registry.tool(description="从运维手册库中检索相关排障文档")
def search_runbook(query: str, circuit_type: str) -> dict:
    ...

@registry.tool(description="查询历史相似故障案例")
def get_historical_incidents(pattern: str, circuit_type: str, limit: int = 3) -> dict:
    ...

@registry.tool(description="测量两点间的网络延迟和丢包率")
def measure_latency(src_node: str, dst_node: str, packet_count: int = 10) -> dict:
    ...

@registry.tool(description="查询 BGP 邻居状态和最近 flap 记录")
def check_bgp_neighbor(device_id: str, tenant_id: str) -> dict:
    ...

@registry.tool(description="查询设备端口状态和错误计数")
def get_port_status(device_id: str, port_id: str, tenant_id: str) -> dict:
    ...

@registry.tool(description="查询任务/工单的当前状态和数据新鲜度")
def get_job_status(job_id: str) -> dict:
    ...
```

统一响应格式：
```json
// 成功
{"ok": true, "data": {...}, "source": "monitoring-api", "as_of": "2026-10-29T15:30:00Z", "request_id": "req-xxx"}

// 失败
{"ok": false, "error": {"code": "timeout", "message": "监控API响应超时", "retryable": true}}
```

对 timeout、rate_limited、forbidden、not_found、invalid_argument 五类错误必须分类处理。

### 2. 记忆与上下文管理（60 分钟）

手写 `DiagnosisMemory` 类，必须实现：

- **短期记忆**：对话历史，超过 6 轮触发压缩
- **降级压缩**：成本超 80% 时，只保留最近 1 轮 + 纪要 + findings 列表
- **长期记忆注入**：历史故障案例按相关性选择性注入（不是全量塞入）
- **关键发现锁定**：一旦 Agent 确认了一个 finding（如"光功率 -12dBm"），压缩时不能丢失

测试场景：
- 10 轮诊断后，前 6 轮被压缩，但"光功率异常"的 finding 仍在上下文中
- 成本降级后，记忆从 3 轮压缩到 1 轮，但关键 finding 不丢失

### 3. 并行诊断 + asyncio（60 分钟）

手写并行诊断逻辑：

```python
async def parallel_diagnosis(engine, circuit_id: str, tenant_id: str):
    """当 Agent 判断需要多角度检查时，并行执行 3 个子任务"""
    tasks = [
        engine.run_sub_agent("circuit_check", [
            ("get_circuit", {"circuit_id": circuit_id, "tenant_id": tenant_id}),
            ("get_port_status", {"device_id": "...", "port_id": "...", "tenant_id": tenant_id}),
        ]),
        engine.run_sub_agent("alarm_analysis", [
            ("list_alerts", {"circuit_id": circuit_id, "tenant_id": tenant_id,
                            "start": "...", "end": "..."}),
        ]),
        engine.run_sub_agent("knowledge_search", [
            ("search_runbook", {"query": "...", "circuit_type": "..."}),
            ("get_historical_incidents", {"pattern": "...", "circuit_type": "..."}),
        ]),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # 处理部分失败：某个子任务超时不影响其他
    return merge_results(results)
```

必须处理：
- 子任务部分失败（1 个超时，2 个成功）→ 合并成功部分，标注 partial
- 子任务全部超时 → 向主循环返回 timeout，不重试写入操作
- 每个子任务有自己的 Token 预算（主预算的 1/3）

### 4. SSE 流式推送（60 分钟）

手写 FastAPI SSE 端点：

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

@app.post("/api/v1/diagnose")
async def create_diagnosis(request: DiagnosisRequest):
    task_id = generate_task_id()
    # 创建 checkpoint 记录
    checkpoint_mgr.create(task_id, request)
    return {"task_id": task_id, "status": "queued"}

@app.get("/api/v1/diagnose/{task_id}/stream")
async def stream_diagnosis(task_id: str, request: Request):
    async def event_generator():
        engine = DiagnosisEngine.from_checkpoint(task_id)
        async for event in engine.run():
            yield {
                "event": event.event_type,
                "id": f"{task_id}-{event.step}",
                "data": json.dumps(event.data, ensure_ascii=False)
            }
    return EventSourceResponse(event_generator())

@app.post("/api/v1/diagnose/{task_id}/confirm")
async def confirm_diagnosis(task_id: str, request: ConfirmRequest):
    # 验证 proposal_hash、actor、过期时间
    ...
```

必须实现：
- 客户端断线重连（`Last-Event-ID` 头），从断点继续推送
- 事件 ID 格式：`{task_id}-{step}-{sequence}`
- 连接超时：30 分钟无事件自动断开
- Prometheus 指标：`diagnosis_events_total{type}`、`diagnosis_sse_connections_active`

### 5. 模型路由 + 成本守卫（60 分钟）

手写 `ModelRouter` 和 `CostGuard`：

```python
class ModelRouter:
    """根据步骤类型和当前成本状态选择模型"""

    ROUTING_TABLE = {
        "classify": ModelTier.LIGHT,       # 告警严重性分类
        "format": ModelTier.LIGHT,         # 参数格式转换
        "tool_select": ModelTier.MEDIUM,   # 选择下一个工具
        "evidence_link": ModelTier.MEDIUM, # 关联多条证据
        "root_cause": ModelTier.HEAVY,     # 根因推理
        "report": ModelTier.HEAVY,         # 报告生成
    }

    def route(self, step_type: str, cost_state: CostState) -> ModelTier:
        if cost_state.is_degraded:
            # 降级：所有步骤最多用 medium
            return min(self.ROUTING_TABLE[step_type], ModelTier.MEDIUM)
        return self.ROUTING_TABLE[step_type]


class CostGuard:
    """Token 预算守卫"""

    def __init__(self, budget: int = 50000):
        self.budget = budget
        self.used = 0
        self.history: list[dict] = []  # 每次调用的 token 记录

    def track(self, input_tokens: int, output_tokens: int, model: str):
        cost = input_tokens + output_tokens
        self.used += cost
        self.history.append({
            "model": model, "input": input_tokens,
            "output": output_tokens, "cumulative": self.used
        })

    @property
    def degradation_level(self) -> str:
        pct = self.used / self.budget
        if pct >= 1.0: return "exhausted"
        if pct >= 0.8: return "degraded"
        if pct >= 0.6: return "warning"
        return "normal"
```

测试场景：
- budget=50000：正常完成 10 步诊断，实际使用 28000 tokens
- budget=15000：第 5 步触发 warning，第 7 步触发 degraded（切换到 aggressive 压缩 + medium 模型）
- budget=8000：第 4 步触发 exhausted，输出 partial report + "budget_exhausted" 事件

### 6. 输出过滤（30 分钟）

手写 `OutputFilter`：

```python
class OutputFilter:
    """诊断报告输出前的安全过滤"""

    # 内部 IP 段（不对外暴露）
    INTERNAL_IP_PATTERNS = [
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}",
        r"192\.168\.\d{1,3}\.\d{1,3}",
    ]

    # 敏感关键词
    SENSITIVE_KEYWORDS = ["password", "secret", "api_key", "token", "credential"]

    def apply(self, report: dict, tenant_config: dict) -> dict:
        """过滤报告内容，返回安全版本"""
        # 1. 内部 IP 脱敏
        # 2. 密码/密钥替换为 [REDACTED]
        # 3. 根据 tenant_config 决定是否脱敏客户名称
        ...
```

### 7. Checkpoint 恢复测试（60 分钟）

手写 6 个恢复测试场景：

| # | 中断点 | 注入方式 | 恢复验证 |
|---|--------|---------|---------|
| 1 | 第 3 步工具调用后 | `os.kill(pid, SIGKILL)` | 重启后从第 4 步继续，前 3 步工具结果复用 |
| 2 | 等待人工确认时 | 进程 kill + 重启 | 仍在等待确认，不默认为批准 |
| 3 | 确认后、报告生成前 | crash_point 注入 | 重查 proposal_hash 和过期时间 |
| 4 | 并行子任务执行中 | kill 一个子任务 | 其他子任务结果保留，失败的标注 partial |
| 5 | 成本降级后 | 降级状态下 crash | 恢复后仍保持降级状态 |
| 6 | 另租户访问相同 task_id | 直接查数据库 | 不泄露任务存在和内容 |

每个测试必须：
- 打开新的数据库连接（不能复用同一对象）
- 验证恢复前后的数据库记录一致性
- 用注入时钟测试过期，不用 `time.sleep()`

## 运行入口与测试

```bash
# 启动诊断服务
python diagnosis_server.py --port 8000

# 运行所有测试
python -m pytest tests/ -v --tb=short

# 单个场景测试
python -m pytest tests/test_checkpoint_recovery.py -v
python -m pytest tests/test_cost_guard.py -v
python -m pytest tests/test_sse_stream.py -v
python -m pytest tests/test_output_filter.py -v
python -m pytest tests/test_parallel_diagnosis.py -v
```

## 故障与验收

### 必须经历的故障

| 故障 | 期望行为 | 不合格做法 |
|------|---------|-----------|
| 工具 API 超时 | 标记 retryable，不重跑写入操作 | 无限重试或静默忽略 |
| 越权查询其他租户电路 | 拒绝 + 审计日志 | 返回数据后在报告中脱敏 |
| Token 预算耗尽 | 终止 + partial report | 继续运行直到自然结束 |
| 进程崩溃 | 从 checkpoint 恢复 | 重新开始整个诊断 |
| SSE 连接断开 | 客户端重连后继续 | 丢失已推送的事件 |
| 并行子任务部分失败 | 合并成功部分 + 标注 partial | 全部失败或静默跳过 |
| 审批过期 | 拒绝执行 | 默认批准 |
| 内容变更后复用旧审批 | 拒绝 + 要求新审批 | 直接执行 |

### 验收清单

- [ ] 3 个故障场景全部正确诊断
- [ ] 崩溃恢复测试 6 个场景全部通过
- [ ] SSE 流延迟 < 1 秒
- [ ] 成本降级和终止行为正确
- [ ] 输出中无内部 IP 明文
- [ ] 并行诊断总耗时 < 串行的 70%
- [ ] 人工门：未确认不归档、过期不执行、变更需重审
- [ ] Prometheus 指标可采集

## 提交与评分

提交 work/ 目录下：
1. `DESIGN.md` — 五项业务决策（谁发起/允许查什么/什么需确认/什么不能重跑/花完怎么结束）
2. `diagnosis_engine.py` — 核心引擎实现
3. `diagnosis_server.py` — FastAPI 服务
4. `tests/` — 至少 6 类故障测试 + 正常流程测试
5. `fixtures/` — 3 个故障场景的完整数据
6. `checkpoint.db` — 恢复测试的数据库快照
7. `METRICS.md` — Token 消耗统计（正常/降级/终止三种场景）
8. `REVIEW.md` — 一页复盘：设计取舍、最大失败风险、什么规模需要升级

评分：业务正确 30 + 长程可靠 25 + 流式与成本 20 + 手写与测试 15 + 复述取舍 10。80 分通过。

## 面试追问

1. **为什么长程 Agent 必须做 checkpoint，而不是靠 max_steps 重试？**
   > 一个 10 步诊断如果从第 5 步崩溃后重头来，前 5 步的工具调用（可能涉及外部 API）就重复执行了。如果工具有写入操作，还可能产生副作用。Checkpoint 保证"从最后成功步骤继续"，工具结果复用、不重复调用。

2. **SSE 和 WebSocket 在 Agent 场景下怎么选？**
   > Agent 诊断是单向推送（服务端→客户端），SSE 更轻量、天然支持重连和 `Last-Event-ID`。WebSocket 适合双向通信（如客户端实时输入修正）。本场景 SSE 足够。

3. **模型路由为什么不让模型自己选？**
   > 模型不知道自己该用哪个模型——它没有成本意识。路由规则是工程逻辑：简单分类用便宜模型，根因推理用贵模型。这比让模型选择可靠 100 倍，而且成本可预测。

4. **成本降级的 80% 阈值怎么定的？**
   > 留 20% 的余量给"终止诊断 + 生成 partial report"这个收尾动作。如果 100% 才降级，收尾动作可能把预算打穿，导致连 partial report 都生成不了。

5. **并行子任务部分失败怎么处理？**
   > 不能因为 1 个子任务超时就否定其他 2 个的成功结果。合并成功的、标注失败的、让主 Agent 决定是否要重试失败的那个。这是"部分降级"而不是"全有或全无"。

6. **Temporal/Inngest 和自己写 checkpoint 有什么区别？**
   > 本质相同：都是"每步存盘，崩溃后恢复"。Temporal 帮你做了 Event Sourcing、自动重试、分布式调度；自己写更轻量但要处理更多边界。生产环境推荐 Temporal，学习阶段手写才能理解原理。
