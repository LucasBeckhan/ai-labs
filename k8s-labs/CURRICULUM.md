# Kubernetes 实战与面试训练路线

> **业务版入口已更新：[6次快速实战](business/FAST-TRACK.md)、[30题任务册](business/DRILLS.md)、[手写清单](business/WRITE-CHECKLIST.md)。** 第一轮用同一云网安沙箱完成交付与故障闭环，再按下面14章补原理；每章BUSINESS-PRACTICE说明业务映射，旧PRACTICE用于第二轮考核，不要求重复抄写。

业务案例参考[中企通信公开服务方向](https://www.china-entercom.com/Product-Services-Summary)，结合用户提到的监控、安全周报、数据治理工作，全部使用虚构数据，不代表公司真实架构和接口。


目标：能从空白配置交付应用，依据证据处理故障，并解释底层机制。原README用于机制参考；新版BUSINESS-PRACTICE与30题任务册是第一轮业务主线，旧PRACTICE用于第二轮加深，Lab11–14补充核心知识。快速主线约6–9小时，完整知识与扩展约40–60小时，按能力推进，不强求固定周数。

## 开始前

1. Docker 运行正常。Lab01 前四步无需 Kubernetes；先直接构建，基础镜像拉取失败再用 hack/prepare-images.sh。build-spark-image.sh 只用于 Lab10 Spark 镜像的备用构建。
2. 创建 labs 前可先准备镜像；创建后重新运行 prepare 导入节点。该脚本报 FAIL 时不能因最后“完成”就认为全部成功。
3. 所有变更前确认 `kubectl config current-context` 为 kind-labs；新版命令显式写 context，旧命令依赖当前 context。Lab14 使用独立 kind-ops。
4. 每章原 manifests 是参考。先创建 work/，从空白写；允许查 `kubectl explain`，不允许复制整份答案。只有软件 API 接受不算成功，必须验证业务结果。server dry-run 不会保存前面文档创建的 SA/namespace 等依赖；依赖不存在时须分阶段验证，不能把这种失败误判为 YAML 字段错误。
5. 旧实验存在 web 等重名对象，Lab03 与 Lab07 不要同时部署在同一 namespace。优先先清理上一章对象，或将自己的练习统一放到独立 namespace。ConfigMap/Secret/Service 等引用须在正确 namespace；集群级对象不受 namespace 隔离。

## 核心能力覆盖与交付物

| 顺序 | 必学知识与场景 | 必须手写 | 故障与验收入口 |
|---|---|---|---|
| 01 | 容器、镜像、CRI 前置、Java 内存 | 多阶段 Dockerfile | [构建成功但启动失败、堆与总内存](lab01-container-basics/PRACTICE.md) |
| 02 | Pod 生命周期、控制平面协作、探针、信号 | Pod、ConfigMap、挂载、三探针 | [挂载失败、Running 不 Ready、更新不生效](lab02-pod-lifecycle/PRACTICE.md) |
| 03 | Deployment/RS、发布、回滚 | 滚动策略与 readiness | [坏镜像、坏探针、发布停滞](lab03-deployment-rollout/PRACTICE.md) |
| 04 | StatefulSet、PVC/PV/SC、CSI、访问模式 | 有状态应用与卷声明 | [PVC Pending、删 Pod 数据保留](lab04-statefulset-storage/PRACTICE.md) |
| 05 | requests/limits、QoS、OOM、限流与驱逐 | 资源边界 | [OOM 证据与 CPU 耗时对照](lab05-resource-oom/PRACTICE.md) |
| 06 | 调度、亲和性、污点、优先级与容量 | 约束与 tolerations | [三类 FailedScheduling](lab06-scheduling/PRACTICE.md) |
| 07 | Pod/Service/DNS/Ingress、EndpointSlice、代理/CNI 分工 | Service、Ingress | [selector、端口、Host 三层故障](lab07-network-ingress/PRACTICE.md) |
| 08 | 排障方法、日志、Events、状态与历史容器 | 修复清单与故障记录 | [五故障限时训练](lab08-troubleshooting/PRACTICE.md) |
| 09 | Metrics API、HPA、容量扩展边界 | autoscaling/v2 | [指标缺失与 requests 分母](lab09-hpa-autoscaling/PRACTICE.md) |
| 10 | Spark driver/executor、监控、RBAC | SA/Role/Binding、抓取配置 | [Forbidden 与 target down](lab10-spark-monitoring/PRACTICE.md) |
| 11 | 配置更新、Secret、认证授权准入、租户隔离与安全上下文 | 配置、最小权限、Quota、LimitRange | [配置、安全和资源隔离](lab11-config-security/README.md) |
| 12 | Job/CronJob、幂等、Helm/Kustomize/GitOps | 批任务、定时任务、overlay | [失败重试与发布流程](lab12-jobs-delivery/README.md) |
| 13 | DNS、网络隔离与 CNI 前置 | DNS 调试对象、NetworkPolicy | [DNS 与网络策略矩阵](lab13-network-policy/README.md) |
| 14 | DaemonSet、拓扑分散、PDB、节点维护、备份恢复与控制平面责任 | 多节点应用、PDB、DaemonSet | [drain、硬故障与恢复](lab14-node-recovery/README.md) |

## 一章如何算学会

先读原理并跑一次健康流程，记录健康基线；合上参考从空白写；每次只引入一个故障，用至少两条证据定位；做最小修复，验证业务并清理；最后用 3 分钟复述机制和取舍。每章保存：work/ 配置、故障记录、恢复输出、面试回答。

统一评分：手写解释 30、证据定位 30、恢复验证 30、复述预防 10；80 分通过。没有修复前证据或功能验证直接重做。单靠截图 Running、复制 YAML、删 Pod 重来不合格。

## 最终综合考核（2–3 小时）

在独立 namespace 从空白部署 2 副本 HTTP 应用，包含资源、探针、配置、Service、最小权限、HPA（指标可用时）。提供一次坏镜像发布与回滚，一次 selector 错误和一次配置更新不生效的完整诊断记录；提交容量与限流说明、备份方案、告警条件。沿用原有可用镜像，任务不依赖自行开发业务服务。

达标条件：集群内请求成功；坏版本不被误判为就绪；回滚后业务恢复；配置更新行为有解释；扩缩容有真实指标；三故障各有证据、修复 diff、回归结果。多节点和策略部分需另提交 Lab13/14 环境证据；未运行必须标注未验证。

## 本地结果与生产能力边界

- 单节点不能证明跨节点高可用、跨可用区容灾或云盘故障切换；多节点 kind 也仍共用一台物理机。
- NetworkPolicy 必须由支持它的网络实现执行；默认 kind 不够。
- hostPath/local-path 不是数据库备份，etcd 快照不等于业务卷备份。
- 集群升级、证书轮换、etcd 恢复、云负载均衡、真实 CSI 快照与 GPU 硬件属于独立环境扩展；面试需解释流程、风险和验收，不能声称本课程已实测。
- 节点/集群自动扩容、VPA、Gateway API、CRD/Operator、设备插件/DRA：掌握用途和边界。平台岗再扩展控制循环、reconcile 幂等、GPU 调度和指标，不作为初学者第一轮手写要求。

## 官方核对依据

[应用排障](https://kubernetes.io/docs/tasks/debug/debug-application/)、[ConfigMap 更新](https://kubernetes.io/docs/tutorials/configuration/updating-configuration-via-a-configmap/)、[NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)、[PDB 与中断](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)。机制以对应集群版本为准。
