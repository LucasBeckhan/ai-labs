# Kubernetes 学习笔记（来自 k8s-labs 实验验证结论）

## 探针与优雅终止
startupProbe 容忍慢启动应用（如 Flink JobManager）；readinessProbe 失败只是从 Service 摘除不重启；livenessProbe 失败会重启容器。Pod 删除时 preStop 先执行，然后 SIGTERM，超过 terminationGracePeriodSeconds 才 SIGKILL；宽限期必须大于应用最长清理时间，否则 Flink checkpoint 丢失、Kafka offset 不提交。

## 资源管理
requests 是调度依据，memory limits 是硬顶（超过即 OOMKilled exit 137），CPU 超限只会被节流。QoS 三级：Guaranteed（requests==limits）、Burstable、BestEffort；节点资源紧张时先驱逐 BestEffort。Java 应用堆用 -XX:MaxRAMPercentage=75 留 25% 给堆外。

## 调度
调度器两阶段：过滤（资源、污点、亲和性）+ 打分。Pending 排查看 describe 的 Events：Insufficient memory / untolerated taint / node affinity 不匹配。GPU 节点打污点防普通任务抢占。

## 网络与 Ingress
Service 通过 label selector 动态维护 Endpoints；集群 DNS 格式 svc.ns.svc.cluster.local。曾经踩坑：NodePort 30080 同时被业务 Service 和 ingress-nginx 占用，流量绕过 Ingress，必须先释放端口再固定 controller 的 NodePort。

## Spark on K8s
cluster 模式下 driver 是 Pod，通过 ServiceAccount 调 K8s API 创建 executor，RBAC 需要 pods/services 的 create/update/patch/delete（patch 权限最容易漏）。executor 容器 args 只有 ["executor"]，真实进程由镜像 entrypoint 拉起 KubernetesExecutorBackend，driver URL 和资源配置全部通过环境变量注入。

## HPA
HPA 每 15 秒从 metrics-server 取指标，期望副本数 = ceil(当前副本 × 实际值/目标值)；CPU 利用率分母是 requests 不是 limits。缩容有稳定窗口（默认 300s，可配 60s），实测窗口后一次性回落到 minReplicas。

## 监控
Prometheus 通过 pod 注解 prometheus.io/scrape 自动发现目标；Prometheus v3 严格要求 /metrics 端点返回 Content-Type: text/plain; version=0.0.4，否则报 non-compliant scrape target。
