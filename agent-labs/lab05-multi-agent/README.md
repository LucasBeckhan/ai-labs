# Lab 05 — 多 Agent 协作：Planner-Executor 模式

> **新版必做：[业务开发、生产故障与验收](BUSINESS-PRACTICE.md)**。原脚本是机制演示，旧“实测”仅指旧用例，不代表新增业务或生产就绪；以新版路线的边界和验收为准。

> **原示例边界校正：** 现有角色演示不能证明生产持久化、事务或完整Schema验证；共享dict和串行执行不提供跨进程恢复。是否采用多Agent必须与Workflow及单Agent比较。



## 📖 本章学习指导
> 建议时长 **2.5 小时** ｜ 前置：agent Lab02 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q13（Agent 本质）

**学习循环：**
1. 读（20min）：plan/execute_step/summarize 三个函数——"提示词窄化"的设计思想
2. 跑（40min）：默认组合任务；观察 Planner 的 3 步计划与 Executor 的逐步执行（含参数纠错）
3. 破坏练习（20min）：① 给 Planner 的提示词加"你也可以直接执行工具"，看输出退化；② 把任务换成 5 步的，看计划质量
4. 验收自测：① 为什么要拆 Planner/Executor（提示词膨胀/注意力稀释）？② "共享黑板"是什么？③ Executor 的参数纠错循环怎么工作？
5. 产出：手画 Planner-Executor 协作时序图

## 核心问答

**Q1：Planner-Executor 分离的设计原理是什么？为什么不直接让一个 Agent 完成所有任务？**

> 核心原因是**提示词窄化**和**注意力稀释**。单 Agent 模式下，系统提示词需要同时包含"规划指令 + 工具描述 + 执行约束"，模型注意力被分散，规划和执行都做不好。
>
> 实测对比（同一组合任务"算 128×64 + 数单词 + 总结"）：
> - **单 Agent**：Planner 阶段就开始尝试执行工具，输出混乱，3 步任务用了 7 步才完成
> - **Planner-Executor 分离**：Planner 专注拆解（3 步清晰计划），Executor 专注执行（每步独立上下文），总步数 5 步
>
> 这是"分而治之"思想在 Agent 设计中的应用——和微服务拆分、数仓分层的逻辑完全一致。

**Q2："共享黑板"在多 Agent 协作中扮演什么角色？如何保证状态一致性？**

> 共享黑板（本实验的 `shared_state` 字典）是多 Agent 的**唯一通信通道**，类似分布式系统中的共享存储。
>
> 本实验的状态一致性保证：
> 1. **串行执行**：Planner → Executor 步骤 1 → Executor 步骤 2 → ... → Summarizer，天然避免并发冲突
> 2. **Schema 校验**：每次写入 shared_state 都经过 Pydantic 校验，防止脏数据
> 3. **不可变历史**：`history` 字段只追加不修改（append-only），保证审计可追溯
>
> 生产环境如果引入并行 Executor（多步骤同时执行），就需要加分布式锁或改用事件溯源（Event Sourcing）——这是从本实验到生产系统的典型演进路径。

**Q3：Executor 的参数纠错循环是如何工作的？为什么要限制最大重试次数？**

> 本实验的 Executor 内置了 3 层防线：
> 1. **Schema 校验**：工具调用前校验参数类型和必填字段，不通过则要求 Planner 修正
> 2. **可读错误返回**：工具执行失败时返回人类可读错误（如"password 长度超出 32"），而非抛异常
> 3. **纠错重试**：Executor 把错误信息反馈给 Planner，要求重新规划该步骤（最多重试 2 次）
>
> 限制最大重试次数的原因：
> - **防止死循环**：实测中 Planner 曾对同一错误反复生成相同参数（模型"固执"现象）
> - **成本可控**：每次重试消耗 LLM tokens，不限制会导致单次任务成本爆炸
> - **快速失败**：超过重试上限后 Summarizer 会标记该步骤为"部分完成"，而非无限等待
>
> 这是 Agent 工程中"防御性编程"的典型实践——和分布式系统的超时重试机制同源。

## 实测记录
任务"算 128×64 + 数单词 + 总结"：Planner 正确拆 3 步（第 3 步 tool_hint 幻觉成 gen_password——Executor 正确忽略）→ 步骤 1 首次传错参数被 Schema 拦截 → 按错误提示修正 → **最终报告 8192 与 4 全对**。三层防线（Schema 校验/可读错误/纠错重试）全部出场的完整案例。

## 运行
```bash
cd ~/Documents/ai-labs/agent-labs/lab05-multi-agent
MODEL=qwen-strong LITELLM_LOCAL_MODEL_COST_MAP=True ~/Documents/ai-labs/llmops-labs/.venv/bin/python planner_executor.py
```
