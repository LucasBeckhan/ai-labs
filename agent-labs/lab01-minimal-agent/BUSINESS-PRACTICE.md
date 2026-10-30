# 网络告警辅助排查：Agent 循环与边界

> 建议 4小时，完成后提交自己的实现和证据。所有业务数据为虚构；原 README/脚本提供机制参考，本页是新增业务必做练习。新版总入口：[业务路线](../CURRICULUM.md)。

## 业务输入与完成边界

值班人员问：“demo-a 的上海分支链路 C-A01 出现丢包，先帮我确认现象和排查方向。”输入不是让 Agent 修复网络，而是收集证据并形成待审核诊断草稿。

先回答：谁发起？要解决什么问题？允许读什么？哪些动作要人工确认？缺数据如何结束？这五项写入 work/README.md 后再编码。

## 从空白手写的任务

1. 手写 Decision、ToolObservation、FinalReport 三个结构，Decision 只允许 get_circuit、search_runbook、final 三种动作。tenant_id、scope 由程序注入，不允许模型传入。
2. 创建 work/network_agent.py，接入 business/sandbox.py；先使用 FakeModel 固定返回“查链路→查手册→final”，再替换为原示例的模型适配器。模型调用与工具执行要分层，不能在 prompt 中当作已经执行。
3. 实现 step<=6、总 deadline、单次模型调用 timeout、重复动作检测；失败应返回 needs_review，并说明缺失证据。temperature=0 不能保证确定性。
4. 最终 JSON 输出 status、observations（含 source/time）、hypotheses、missing_evidence、next_checks、citations。严禁把工具缺失或超时解释成链路正常。
5. 增加 FakeModel：连续返回同一工具、返回无效 JSON、无工具直接声称根因。分别记录程序如何结束；不要求存储模型隐含思维，只保留可审计动作与理由摘要。

## 运行入口与参考边界

运行 `python3 ../business/sandbox.py --scenario network`（命令从本章目录执行）读取基线；用自己的决策循环复现结果。另用 FakeModel 跑重复、格式错误、无证据断言三例，不调用外网。

模型阶段不限定框架。优先沿用原有模型网关适配器，但密钥从环境/Secret获取，不复用旧例子中的硬编码演示值。离线FakeModel验证控制逻辑，真实模型验证工具选择和回答质量，两者分别报告。

## 故障与验收

正常：loss_pct=8.5，引用 KB-001，只说“观测到丢包，根因待确认”。timeout：needs_review。跨租户 C-B01：未找到可访问对象。输出必须含未查询接口计数/近期变更等证据缺口。

每个故障保存：输入、身份、关键trace、错误码、根因、最小修复、恢复结果、预防措施。对照 [生产故障表](../business/FAILURE-DRILLS.md)，不要把单纯重跑成功当修复。

## 提交与评分

提交 work/代码、配置、可复跑测试、结果JSON/日志和一页复盘。业务正确30分、边界与失败处理30分、手写与测试25分、复述取舍15分；80分通过，越权/无审批写入/敏感数据泄露直接重做。引用和数值须与fixture一致；未运行部分标记未验证。

## 面试追问

为什么这里保留 Agent 的工具选择，而不是允许直接执行 CLI？max_steps 能否替代网络超时？循环检测会不会阻止合理的定时复查？

结合本章实际证据，用“业务目标→设计→故障→定位→修复→取舍”作答；实验不得包装成公司生产项目。
