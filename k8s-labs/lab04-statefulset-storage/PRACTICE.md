# 持久化、卷故障与恢复：独立练习与验收

> 前置：先完成本章 README 的正常流程。本页才是必做考核；原 manifests/app 文件是参考答案，先合上再写。仅在本地 kind-labs 练习，禁止对生产上下文执行故障注入。

## 先明确边界

kind local-path 存储不是云盘容灾；删除 kind 集群可能丢失节点内的数据。先备份再进行删除演练。

## 第一轮：手写（30–45 分钟）

手写 Secret、Headless Service、1 副本 StatefulSet 和 volumeClaimTemplates；列明 serviceName、卷名、mountPath 的对应关系。

在本章创建自己的 `work/` 目录；不要覆盖参考文件。先口述每个字段的作用，再写 YAML。允许查 `kubectl explain` 和官方 API 文档，不允许整段复制答案。应用前执行 `kubectl --context kind-labs apply --dry-run=server -f work/`（Dockerfile 不适用）；dry-run 仅验证 API 可接受，不证明程序可运行。

产出：PVC/PV/StorageClass 清单；建表写入测试行；删除 Pod 后数据仍在的查询输出。

## 第二轮：故障注入与恢复（30–45 分钟）

A：在新的练习 PVC 上填写不存在的 storageClassName，观察 Pending 和 Events。B：删除数据库 Pod，观察原 PVC 被重新使用；不删除存量 PVC。

每次先保存健康基线，写下预期，再注入一个故障；按 [排障记录模板](../INCIDENT-TEMPLATE.md) 保存证据。只修改自己的练习对象。涉及节点污点或限额时，先记录原值，结束恢复原值。

验收：A：定位 provisioner/StorageClass，不将 Pending 直接归因于 CPU。B：重建后查到原测试行；同时说明这不能证明节点丢失可恢复。

## 第三轮：面试复述（5 分钟）

StatefulSet 保证数据库高可用吗？RWO 是否等于同一时刻只允许一个 Pod？

回答必须包含一次亲自观测的证据，使用“现象→机制→定位→修复→副作用”结构。不能将本地实验称为生产经历。

## 自查答案（完成后再打开）

<details>
<summary>定位线索与参考</summary>

kind local-path 存储不是云盘容灾；删除 kind 集群可能丢失节点内的数据。先备份再进行删除演练。

本章 README 与原有清单提供基础参考；故障答案以实际 Events、日志和条件为准。若观测与预期不同，先排除镜像不可用、集群上下文错误、旧对象未清理、指标组件未就绪，再修改实验结论。

</details>

## 评分与清理

- 手写与解释：30 分；字段正确且能解释引用关系。
- 定位与证据：30 分；保留修复前状态，不凭猜测操作。
- 恢复与功能验证：30 分；修复后验证请求、数据或任务结果。
- 面试复述与预防：10 分；说清适用边界。

80 分合格，缺少故障证据或恢复验证直接重做。记录实际资源名后逐项删除自己的练习对象；共享组件和数据库 PVC 不自动删除。不要用删除整个集群代替清理。
