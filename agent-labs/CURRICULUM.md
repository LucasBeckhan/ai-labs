# Agent与Workflow：面向云、网、安业务的工程训练

## 学习目标和业务依据

以大数据架构师的基础出发：不是练“聊天机器人能说什么”，而是能把可信数据接入模型、约束执行边界、验证业务结果，并交付可运营服务。主线是只读网络告警诊断；副线是安全周报、知识助手和数据任务健康。所有案例都是依据公开业务方向与用户描述设计的训练假设，不代表公司真实架构、接口、SLA或内部制度。

公开依据：中企通信官网介绍网络连接、信息安全、云计算、云数据中心服务，以及相关运营支撑；据此选用云网安场景，不推断内部系统已开放任何接口。参见[公司介绍](https://www.china-entercom.com/about-china-entercom)、[产品服务](https://www.china-entercom.com/Product-Services-Summary)。用户提及的网络监控、安全周报、内部数据治理、Token平台用作练习背景，不视为已获真实系统接入权限。

## 你最终要交付什么

1. 网络诊断助手：输入资产与现象，读取授权范围内的链路/告警/手册，输出含时间、证据、假设和缺口的诊断草稿，不自动修改网络。
2. 安全运营周报：固定流程确定性统计，模型解释；有数据质量校验、引用、审核与重复运行治理。
3. 可运营接口：身份/租户隔离、预算、观测、限流、错误分类；长任务状态与人工审批能在重启后恢复。

附加业务选择：DolphinScheduler失败任务排查、数据质量异常解释、云资源费用异常分析、售前知识问答。先完成主线再扩展，不在第一轮同时做所有场景。

## 先分清三种实现

| 方式 | 谁决定下一步 | 本课程中适用任务 | 验证重点 |
|---|---|---|---|
| Workflow | 程序预定状态/分支 | 周报采集聚合、审批发布 | 状态、口径、幂等、异常路径 |
| 单Agent | 模型在受限工具中选择 | 探索性告警排查、查询改写 | 证据、工具选择、预算、结束条件 |
| 多Agent | 多个受限角色协作 | 跨云/网/安的复杂诊断对照实验 | 部分失败、冲突、协调成本 |

默认先用最简单的可验证方案。一个固定三步调用LLM的程序仍是Workflow；多个函数不自动等于多个Agent。业务状态、租户授权和审批不由模型自由决定。

## 路线与必须手写项（约40–50小时）

先完成各章原README的机制演示，再合上参考完成BUSINESS-PRACTICE；Lab09/10直接按README实践。当前新增的可执行参考仅business/中的离线工具与基线，业务Agent、API、SDK版MCP和持久化审批是必须自己完成的训练任务，并非已交付生产实现。

| 章 | 业务与核心能力 | 必须手写 | 必须经历的失败 |
|---|---|---|---|
| [01](lab01-minimal-agent/BUSINESS-PRACTICE.md) | 网络告警诊断循环 | 决策/观察/最终报告schema、FakeModel与有界循环 | 重复、格式错误、无证据断言 |
| [02](lab02-tool-registry/BUSINESS-PRACTICE.md) | 工具契约与授权 | schema、执行器、新数据任务工具、重试 | 越权、timeout、非法参数 |
| [03](lab03-agent-memory/BUSINESS-PRACTICE.md) | 工单上下文与记忆 | SQLite会话、TTL、版本冲突、清除 | 串租户、过期、重启、并发覆盖 |
| [04](lab04-agentic-rag/BUSINESS-PRACTICE.md) | 运维知识与合同问答 | ACL索引、检索基线、引用校验 | 过期文档、无SLA、检索注入 |
| [05](lab05-multi-agent/BUSINESS-PRACTICE.md) | 云网安协同诊断 | 三方案对照、证据包、partial状态 | 子任务失败、冲突、成本增加 |
| [06](lab06-mcp-protocol/BUSINESS-PRACTICE.md) | 企业只读工具MCP | 锁定SDK/协议、身份适配、错误映射 | 版本不兼容、无权调用、取消 |
| [07](lab07-agent-eval-safety/BUSINESS-PRACTICE.md) | 业务评估与安全 | 30例测试、报告、回归门禁 | 越权、注入、幻觉、正常任务误拒 |
| [08](lab08-agent-production/BUSINESS-PRACTICE.md) | API与云原生交付 | POST接口、限流/预算、指标、容器配置 | 队列满、429、取消、重启 |
| [09](lab09-business-workflow/README.md) | 安全周报Workflow | 口径、聚合器、解释/核对、版本 | 分页漏数、重复、边界、错数 |
| [10](lab10-durable-approval/README.md) | 审批与可靠执行 | checkpoint、状态机、审批hash、幂等 | 审批过期、重复回调、崩溃恢复 |

建议顺序01→02→03→04→09→07→05→06→10→08，先做一个有业务结果的Workflow，再补协作和交付。初学阶段第一周只完成01/02，不必同时学习框架、向量库和K8s。

## 一章的学习流程

- 先口述业务：谁使用、什么输入、期望输出、什么是错误结果、哪些动作不能自动做。
- 跑离线参考，记录正常基线；从空白写自己的schema/函数/配置，允许查文档，不整段抄答案。
- 用FakeModel返回固定动作，证明控制逻辑；接真实模型验证选择和表达。两层结果分开报告。
- 每次只注入一个故障，保存修复前证据；修复后验证业务结果与边界，不只看HTTP 200。
- 用三分钟解释设计、错误、恢复、代价，写入work/复盘。案例是学习实验，不包装成公司生产上线经历。

统一评分：业务正确30、安全和失败处理30、手写与测试25、复述与取舍15；80分通过。越权读取、无审批写入、敏感信息泄漏直接不通过。具体实验要求以章节为准。

## 现在就能运行的基线

在agent-labs目录：

```bash
python3 business/sandbox.py --scenario network
python3 business/sandbox.py --scenario report
python3 business/sandbox.py --scenario timeout
python3 business/sandbox.py --scenario cross-tenant
python3 -m unittest discover -s business/tests -v
```

不需要模型、网关、云账户或新依赖。network输出是确定性草稿，不是模型诊断；12项测试验证工具边界，不证明模型评估或生产可用性。每个章节work/自行存放，勿覆盖参考脚本。

## 业务数据与架构职责

```text
用户/API → 认证与租户上下文 → 任务状态/Workflow
                              ↓
                        受限Agent决策
                              ↓
                       工具执行器/授权
                  ↙           ↓           ↘
             监控适配器    告警/任务适配器    ACL知识检索
                              ↓
                    证据与数值校验 → 草稿
                              ↓
                     人工审核 → 模拟归档
```

工程师负责可靠的业务工具与口径，模型负责受限选择和解释。可将Kafka/Flink用于事件去重、窗口聚合，Doris用于分析，DolphinScheduler用于定时报表；这是对既有能力的迁移建议，不代表生产必须用全部组件。先用本地JSON/SQLite完成闭环，再按数据量决定技术选型。

## 生产要求与业务验收

| 维度 | 要练的内容 | 不合格的替代做法 |
|---|---|---|
| 数据正确 | 时间窗、去重、数据版本、新鲜度、缺失 | 让模型心算统计、失败填0 |
| 权限隔离 | 服务端身份、逐工具授权、检索ACL | 提示词写“不要越权” |
| 行动边界 | 只读默认、hash绑定审批、幂等 | 模型回复“已获批”即执行 |
| 可靠运行 | timeout/取消、退避、队列、checkpoint | 只有max_steps或无限重试 |
| 效果评估 | 正负样本、holdout、回归与人工复核 | 几道演示题成功即称准确率高 |
| 运行观测 | request/tool trace、Histogram、usage、错误率 | 输出所有客户原文、用request_id做指标label |
| 云原生 | 镜像、Secret、资源、健康、持久化 | hostNetwork+单进程字典就称生产架构 |

## 毕业验收与可选扩展

一场30分钟演示：网络诊断正常→工具timeout→越权查询→过期手册；周报重复/漏页→数值校验；审批前重启→恢复→重复审批回调。至少30例评估有机器报告，引用/统计与fixture一致。真实模型部分按模型版本记录调用数、token、P50/P95与成本来源，不虚构供应商价格。

最后写一页架构决策：为何用Workflow/Agent、何处需要模型、权限在哪里保证、哪些操作保留人工、当前最大失败风险、什么规模才需要升级存储/队列。

可选框架迁移：完成零框架后，选一个能表达图状态/checkpoint的框架重写Lab09/10，锁定版本，复用同一验收集，对比恢复/调试/依赖成本；不以框架数量计分。其他扩展：SSE进度、模型路由与Token平台、只读SQL模板、数据质量助手。任意SQL/shell和真实网络配置下发不作为默认工具。

## 参考与版本边界

- [MCP规范仓库](https://github.com/modelcontextprotocol/modelcontextprotocol)、[2026-07-28规范说明](https://blog.modelcontextprotocol.io/posts/2026-07-28/)：旧mini_mcp固定2024-11-05，新练习必须按锁定版本实现，不能把旧握手当作所有版本要求。
- [OpenTelemetry通用追踪规范](https://opentelemetry.io/docs/specs/semconv/general/trace/)：先实现稳定的业务追踪，扩展GenAI属性前核对所选SDK与约定版本。

旧章节“生产级/实测通过”仅是历史演示描述，不能替代本路线的鉴权、恢复、负载和业务评估。新增课程以实际测试报告为准。
