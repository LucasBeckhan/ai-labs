# 发布、回滚与可用性：独立练习与验收

> 前置：先完成本章 README 的正常流程。本页才是必做考核；原 manifests/app 文件是参考答案，先合上再写。仅在本地 kind-labs 练习，禁止对生产上下文执行故障注入。

## 先明确边界

Deployment 控制 ReplicaSet，后者控制 Pod；PDB 不限制 Deployment 自己的滚动发布。

## 第一轮：手写（30–45 分钟）

手写 3 副本 Deployment：selector 与 template labels 匹配；readiness、requests/limits、maxSurge=1、maxUnavailable=0、progressDeadlineSeconds=60。

在本章创建自己的 `work/` 目录；不要覆盖参考文件。先口述每个字段的作用，再写 YAML。允许查 `kubectl explain` 和官方 API 文档，不允许整段复制答案。应用前执行 `kubectl --context kind-labs apply --dry-run=server -f work/`（Dockerfile 不适用）；dry-run 仅验证 API 可接受，不证明程序可运行。

产出：发布前后 ReplicaSet、Pod、rollout history 证据；变更 YAML 和回滚记录。

## 第二轮：故障注入与恢复（30–45 分钟）

A：把镜像改成不存在的标签，观察旧副本和新副本。B：恢复镜像、把新模板 readiness 路径改错。分别观察发布停滞并回滚。

每次先保存健康基线，写下预期，再注入一个故障；按 [排障记录模板](../INCIDENT-TEMPLATE.md) 保存证据。只修改自己的练习对象。涉及节点污点或限额时，先记录原值，结束恢复原值。

验收：在终端 watch 中看到旧 Ready 副本保留；rollout status 超时后诊断 Events；undo 后验证实际镜像和 Ready 数，而非只看命令成功。

## 第三轮：面试复述（5 分钟）

maxUnavailable=0 就一定零故障吗？回滚是否回滚数据库、ConfigMap？

回答必须包含一次亲自观测的证据，使用“现象→机制→定位→修复→副作用”结构。不能将本地实验称为生产经历。

## 自查答案（完成后再打开）

<details>
<summary>定位线索与参考</summary>

Deployment 控制 ReplicaSet，后者控制 Pod；PDB 不限制 Deployment 自己的滚动发布。

本章 README 与原有清单提供基础参考；故障答案以实际 Events、日志和条件为准。若观测与预期不同，先排除镜像不可用、集群上下文错误、旧对象未清理、指标组件未就绪，再修改实验结论。

</details>

## 评分与清理

- 手写与解释：30 分；字段正确且能解释引用关系。
- 定位与证据：30 分；保留修复前状态，不凭猜测操作。
- 恢复与功能验证：30 分；修复后验证请求、数据或任务结果。
- 面试复述与预防：10 分；说清适用边界。

80 分合格，缺少故障证据或恢复验证直接重做。记录实际资源名后逐项删除自己的练习对象；共享组件和数据库 PVC 不自动删除。不要用删除整个集群代替清理。
