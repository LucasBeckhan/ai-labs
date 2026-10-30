# 把监控与资产查询封装成可信工具

> 建议 4小时，完成后提交自己的实现和证据。所有业务数据为虚构；原 README/脚本提供机制参考，本页是新增业务必做练习。新版总入口：[业务路线](../CURRICULUM.md)。

## 业务输入与完成边界

Agent 要调用“链路状态、告警列表、知识手册”三种后端。模型能填参数不代表有权限，也不代表返回数据新鲜。

先回答：谁发起？要解决什么问题？允许读什么？哪些动作要人工确认？缺数据如何结束？这五项写入 work/README.md 后再编码。

## 从空白手写的任务

1. 手写三个工具的 JSON Schema：get_circuit(circuit_id)、list_alerts(start,end)、search_runbook(query)，禁止额外参数，明确范围和时间格式。参考 Sandbox 的严格拒绝行为，不沿用原例子的随意字符串转数值和范围裁剪来处理资产/金额/权限参数。
2. 手写统一响应 ok/data/source/as_of/request_id 或 ok=false/error(code,message,retryable)；对 timeout、rate_limited、forbidden、not_found、invalid_argument 分类。
3. 手写带身份上下文的执行器：认证在 API 边界完成，授权在每次工具调用时再次检查；通过用户输入 tenant_id 选择租户的实现不合格。
4. 新增查询模拟任务健康状态工具 get_job_status(job_id)，返回 status、observed_at、last_success_at、source。任务信息自己增加到独立 fixture，包含一个“成功但数据未更新”的反例。
5. 实现有界重试：只有可重试的只读失败才重试，总尝试最多3次，指数退避加抖动，并服从总 deadline；认证/参数错误不重试。用可注入 clock/sleep 避免测试真的等待。

## 运行入口与参考边界

从 agent-labs 运行 `python3 -m unittest discover -s business/tests -v`，再在 work/ 为新工具增加正常、越权、参数错误、依赖超时、过期数据五类测试。

模型阶段不限定框架。优先沿用原有模型网关适配器，但密钥从环境/Secret获取，不复用旧例子中的硬编码演示值。离线FakeModel验证控制逻辑，真实模型验证工具选择和回答质量，两者分别报告。

## 故障与验收

非法租户参数被拒；缺少 ops:read 无法查询；timeout 不泄露内部堆栈。告警统计 raw_count=3、unique_count=2，不包含窗口右边界；新工具不能把进程存活当作数据新鲜。

每个故障保存：输入、身份、关键trace、错误码、根因、最小修复、恢复结果、预防措施。对照 [生产故障表](../business/FAILURE-DRILLS.md)，不要把单纯重跑成功当修复。

## 提交与评分

提交 work/代码、配置、可复跑测试、结果JSON/日志和一页复盘。业务正确30分、边界与失败处理30分、手写与测试25分、复述取舍15分；80分通过，越权/无审批写入/敏感数据泄露直接重做。引用和数值须与fixture一致；未运行部分标记未验证。

## 面试追问

为什么工具描述和 Schema 不能替代授权？哪些错误要反馈模型，哪些必须终止？为什么生产不应直接把 str(exception) 返回用户？

结合本章实际证据，用“业务目标→设计→故障→定位→修复→取舍”作答；实验不得包装成公司生产项目。
