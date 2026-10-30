# Agent与Workflow开发实验室：面向云网安业务

> 面向有大数据架构基础、希望开发和交付AI应用的学习者。结合中企通信公开业务方向及网络监控、安全周报、数据治理场景，使用虚构数据练习，默认不连接任何公司系统。

**学习入口：[业务路线、知识矩阵与验收](CURRICULUM.md)**。原8章保留机制演示，每章新增BUSINESS-PRACTICE，另增Workflow与持久化审批两章。先明确业务结果，再手写、故障注入和恢复；原脚本不是生产模板。

| 章节 | 学什么 | 业务练习 |
|---|---|---|
| [01 最小Agent](lab01-minimal-agent/README.md) | 决策循环、工具、预算与终止 | [网络告警诊断](lab01-minimal-agent/BUSINESS-PRACTICE.md) |
| [02 工具体系](lab02-tool-registry/README.md) | Schema、参数、授权、错误与重试 | [监控/资产/数据任务工具](lab02-tool-registry/BUSINESS-PRACTICE.md) |
| [03 记忆](lab03-agent-memory/README.md) | 会话、TTL、事实、并发、持久化 | [工单上下文隔离](lab03-agent-memory/BUSINESS-PRACTICE.md) |
| [04 Agentic RAG](lab04-agentic-rag/README.md) | 检索、ACL、版本、引用与拒答 | [运维知识助手](lab04-agentic-rag/BUSINESS-PRACTICE.md) |
| [05 多Agent](lab05-multi-agent/README.md) | 规划、证据融合、部分失败与成本 | [云网安协同诊断对照](lab05-multi-agent/BUSINESS-PRACTICE.md) |
| [06 MCP](lab06-mcp-protocol/README.md) | 协议版本、工具暴露、身份与错误 | [只读业务工具MCP](lab06-mcp-protocol/BUSINESS-PRACTICE.md) |
| [07 评估与安全](lab07-agent-eval-safety/README.md) | 业务指标、攻击测试、回归 | [30例业务评估](lab07-agent-eval-safety/BUSINESS-PRACTICE.md) |
| [08 生产交付](lab08-agent-production/README.md) | API、队列、预算、观测与K8s | [诊断服务交付](lab08-agent-production/BUSINESS-PRACTICE.md) |
| [09 业务Workflow](lab09-business-workflow/README.md) | 确定性统计、解释与审核 | 安全运营周报 |
| [10 可靠执行](lab10-durable-approval/README.md) | Checkpoint、审批、幂等与恢复 | 审批后模拟归档 |

## 现在先做什么

建议按01→02→03→04→09→07→05→06→10→08学习。先跑不依赖模型的参考：

```bash
cd /Users/hp/Documents/ai-labs/agent-labs
python3 business/sandbox.py --scenario network
python3 business/sandbox.py --scenario report
python3 -m unittest discover -s business/tests -v
```

[公共工具说明](business/README.md)解释哪些功能已实现、哪些需要自己写。新增离线代码只依赖Python标准库；旧模型脚本依赖原有llmops虚拟环境与网关。模型密钥从环境或Secret提供，不沿用硬编码演示密钥。

## 课程边界

目前新增可执行参考为离线数据、只读工具、确定性Workflow和12项边界测试；章节中的业务Agent、SDK版MCP、生产API、审批恢复是学生必须实现的练习，不能视为现成产品。旧“实测”记录仅针对旧用例，不代表新业务训练已在公司环境验证。

所有客户、线路、事件均为虚构，不包含真实接口和凭据。训练范围默认只读；发布/变更只模拟，不能自动下发设备配置、封禁IP、发送客户报告或修改工单。后续接真实系统时再按公司权限与发布流程执行。

相关能力：[LLMOps](../llmops-labs/README.md)、[K8s实战路线](../k8s-labs/CURRICULUM.md)、[面试准备](../interview-prep/06-llmops-ai-infra.md)。
