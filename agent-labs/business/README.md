# 业务模拟工具与离线参考

这是新增业务练习的公共底座，仅使用Python标准库。数据全部虚构；没有公司凭据、接口、客户信息。当前实现是**确定性Workflow与工具契约参考**，不是LLM Agent、完整MCP服务或生产系统。

从agent-labs目录执行：

```bash
python3 business/sandbox.py --scenario network
python3 business/sandbox.py --scenario report
python3 business/sandbox.py --scenario timeout
python3 business/sandbox.py --scenario cross-tenant
python3 -m unittest discover -s business/tests -v
```

| 场景 | 预期 |
|---|---|
| network | draft；loss_pct=8.5；引用KB-001；根因待确认 |
| report | raw_count=3，unique_count=2，半开窗口 |
| timeout | needs_review，不能声称链路正常 |
| cross-tenant | needs_review，not_found，不泄露另一个租户的资产 |

## 工具契约

| 工具 | 模型可填的参数 | 服务端负责 | 输出 |
|---|---|---|---|
| get_circuit | circuit_id | 从可信Context获取tenant/scope并过滤 | status、指标、observed_at、stale |
| list_alerts | start/end带时区，最多7天 | 租户过滤、窗口、event_id去重 | raw/unique count、event_ids |
| search_runbook | query | 先租户/有效版本过滤再检索 | 有效doc_id/version/body |

call返回统一的ok/data或error，并带request_id。禁止模型传tenant_id。Context只模拟认证后身份：**Context构造函数不是认证功能**；服务端必须验证真实身份后才能创建它。

## 有意保留的练习缺口

- 没有LLM决策、真正网络超时、退避重试、分页、持久化、认证网关、并发或API。
- timeout/rate_limited为立即返回的故障注入，不是线程/网络超时实现。
- search_runbook只是关键词基线，不是向量RAG或抗注入系统。
- 时间以fixture.as_of为基准，便于可重复测试；接线上后需真实时钟和采样时效。
- 无写工具；审批、模拟发布、恢复由Lab10要求学生实现。
- 12例只验证确定性边界，不证明模型选择能力、抗注入成功率或业务整体效果。

建议先运行读输出，再合上参考实现自己的工具；不要只修改几个名字当作完成业务训练。
