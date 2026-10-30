# Pod 生命周期与配置挂载：独立练习与验收

> 前置：先完成本章 README 的正常流程。本页才是必做考核；原 manifests/app 文件是参考答案，先合上再写。仅在本地 kind-labs 练习，禁止对生产上下文执行故障注入。

## 先明确边界

文件更新没有固定一分钟保证；环境变量不自动更新；subPath 挂载不接收后续 ConfigMap 更新。

## 第一轮：手写（30–45 分钟）

从空白写 webapp-code ConfigMap 和 webapp Pod；Python 代码可复用，必须手写 volumes、volumeMounts、command、三种探针、resources 和优雅退出配置。

在本章创建自己的 `work/` 目录；不要覆盖参考文件。先口述每个字段的作用，再写 YAML。允许查 `kubectl explain` 和官方 API 文档，不允许整段复制答案。应用前执行 `kubectl --context kind-labs apply --dry-run=server -f work/`（Dockerfile 不适用）；dry-run 仅验证 API 可接受，不证明程序可运行。

产出：work/ 下两份 YAML；画出 ConfigMap 键 server.py 到 /app/server.py 的关系。

## 第二轮：故障注入与恢复（30–45 分钟）

A：把 configMap.name 改为 missing-code；观察 Events 后恢复。B：把 readiness 路径改错，检查 Running 和 Ready 的差别。C：把日志文本改为 VERSION2，只更新 ConfigMap，分别观察挂载文件和运行进程。

每次先保存健康基线，写下预期，再注入一个故障；按 [排障记录模板](../INCIDENT-TEMPLATE.md) 保存证据。只修改自己的练习对象。涉及节点污点或限额时，先记录原值，结束恢复原值。

验收：A：出现 FailedMount，修复引用恢复。B：Ready=False，但仅 readiness 失败不会导致重启。C：文件最终更新，原 Python 进程不会自动重载；重建练习 Pod 后新日志生效。

## 第三轮：面试复述（5 分钟）

startup 为什么能保护慢启动？preStop 是否占用宽限期？删除 Pod 和容器重启区别？

回答必须包含一次亲自观测的证据，使用“现象→机制→定位→修复→副作用”结构。不能将本地实验称为生产经历。

## 自查答案（完成后再打开）

<details>
<summary>定位线索与参考</summary>

文件更新没有固定一分钟保证；环境变量不自动更新；subPath 挂载不接收后续 ConfigMap 更新。

本章 README 与原有清单提供基础参考；故障答案以实际 Events、日志和条件为准。若观测与预期不同，先排除镜像不可用、集群上下文错误、旧对象未清理、指标组件未就绪，再修改实验结论。

</details>

## 评分与清理

- 手写与解释：30 分；字段正确且能解释引用关系。
- 定位与证据：30 分；保留修复前状态，不凭猜测操作。
- 恢复与功能验证：30 分；修复后验证请求、数据或任务结果。
- 面试复述与预防：10 分；说清适用边界。

80 分合格，缺少故障证据或恢复验证直接重做。记录实际资源名后逐项删除自己的练习对象；共享组件和数据库 PVC 不自动删除。不要用删除整个集群代替清理。
