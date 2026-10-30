# 服务发现与请求链路：独立练习与验收

> 前置：先完成本章 README 的正常流程。本页才是必做考核；原 manifests/app 文件是参考答案，先合上再写。仅在本地 kind-labs 练习，禁止对生产上下文执行故障注入。

## 先明确边界

排查顺序：进程监听→Pod IP→Service/EndpointSlice→DNS→Ingress；Ingress 对象需要 Controller 才工作。

## 第一轮：手写（30–45 分钟）

手写 Deployment、ClusterIP Service、Ingress；标注 selector、port、targetPort、host、path 和 ingressClassName。

在本章创建自己的 `work/` 目录；不要覆盖参考文件。先口述每个字段的作用，再写 YAML。允许查 `kubectl explain` 和官方 API 文档，不允许整段复制答案。应用前执行 `kubectl --context kind-labs apply --dry-run=server -f work/`（Dockerfile 不适用）；dry-run 仅验证 API 可接受，不证明程序可运行。

产出：从同命名空间调试 Pod 到 Service、再到 Ingress 的请求证据；EndpointSlice 清单。

## 第二轮：故障注入与恢复（30–45 分钟）

A：Service selector 改错。B：恢复后将 targetPort 改为无人监听端口。C：请求错误 Host。每次只引入一个故障。

每次先保存健康基线，写下预期，再注入一个故障；按 [排障记录模板](../INCIDENT-TEMPLATE.md) 保存证据。只修改自己的练习对象。涉及节点污点或限额时，先记录原值，结束恢复原值。

验收：A：EndpointSlice 无匹配后端；B：有后端但目标端口错误；C：区分 Ingress 路由与后端故障，记录实际 HTTP 状态。

## 第三轮：面试复述（5 分钟）

containerPort 声明会让程序开始监听吗？DNS 解析成功为何仍可能连接失败？

回答必须包含一次亲自观测的证据，使用“现象→机制→定位→修复→副作用”结构。不能将本地实验称为生产经历。

## 自查答案（完成后再打开）

<details>
<summary>定位线索与参考</summary>

排查顺序：进程监听→Pod IP→Service/EndpointSlice→DNS→Ingress；Ingress 对象需要 Controller 才工作。

本章 README 与原有清单提供基础参考；故障答案以实际 Events、日志和条件为准。若观测与预期不同，先排除镜像不可用、集群上下文错误、旧对象未清理、指标组件未就绪，再修改实验结论。

</details>

## 评分与清理

- 手写与解释：30 分；字段正确且能解释引用关系。
- 定位与证据：30 分；保留修复前状态，不凭猜测操作。
- 恢复与功能验证：30 分；修复后验证请求、数据或任务结果。
- 面试复述与预防：10 分；说清适用边界。

80 分合格，缺少故障证据或恢复验证直接重做。记录实际资源名后逐项删除自己的练习对象；共享组件和数据库 PVC 不自动删除。不要用删除整个集群代替清理。
