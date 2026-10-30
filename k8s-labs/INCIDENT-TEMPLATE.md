# 故障记录模板

复制到自己的 work/incident-日期.md；保存日志时脱敏，不提交凭据。

- 场景、时间、context、namespace、对象名：
- 健康基线与用户影响（请求/延迟/数据/任务结果）：
- 注入的单个变更（练习时填写）：
- 证据 1：命令 + 关键输出 + 时间：
- 证据 2：命令 + 关键输出 + 时间：
- 假设与排除过程：
- 根因、触发条件、影响范围：
- 临时止血与风险：
- 最小修复（配置 diff）：
- 修复后的功能验证、Ready、重启、指标：
- 回滚方法与触发条件：
- 预防：配置校验、监控告警、容量或发布策略：
- 清理对象与剩余资源：

## 采证起点

以下只读命令使用自己的命名空间与 Pod 名替换占位符；先确认上下文。

```bash
kubectl config current-context
kubectl --context kind-labs -n <namespace> get pods -o wide
kubectl --context kind-labs -n <namespace> describe pod <pod>
kubectl --context kind-labs -n <namespace> logs <pod> --all-containers --tail=100
kubectl --context kind-labs -n <namespace> logs <pod> --previous --tail=100
kubectl --context kind-labs -n <namespace> get events --sort-by=.metadata.creationTimestamp
```

previous 没有输出可能是没有上一轮容器；Events 有保留期限；这两者不是持久日志系统。不得在报告里粘贴 Secret 内容。
