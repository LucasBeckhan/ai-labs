# 多节点维护、PDB 与恢复演练

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> 使用新版训练路线；每次实验提交 YAML、故障证据、恢复验证和面试复述，按 [统一验收](../CURRICULUM.md) 评分。参考清单用于核对，必须先手写。

## 环境与风险边界

本章单独创建 `ops` 集群，不删改原 labs。至少准备 3 个节点的内存额度，镜像准备脚本只加载 labs，**不会自动加载 ops**。下面命令固定 ops context。生产节点维护还需要容量、SLO、存储与变更窗口评估。

```bash
kind create cluster --name ops --config kind-ops.yaml
kind load docker-image nginx:1.27 busybox:1.36 --name ops
kubectl --context kind-ops create namespace k8s-practice-14
kubectl --context kind-ops -n k8s-practice-14 apply -f reference.yaml
kubectl --context kind-ops -n k8s-practice-14 rollout status deployment/web --timeout=180s
kubectl --context kind-ops -n k8s-practice-14 get pods -o wide
```

若本机缺镜像，先 docker pull；节点镜像 kindest/node:v1.31.4 也需可获取。本章 reference 使用 hostname 拓扑分散，检查两个 worker 各有一个 web Pod。

## 手写与维护（90 分钟）

先独立写：2 副本 Deployment、readiness、resources、topologySpreadConstraints（hostname，maxSkew=1，DoNotSchedule）与 minAvailable=1 的 PDB，再对照参考。

```bash
kubectl --context kind-ops -n k8s-practice-14 get pdb
kubectl --context kind-ops drain ops-worker --ignore-daemonsets --timeout=90s
kubectl --context kind-ops -n k8s-practice-14 get pods -o wide
kubectl --context kind-ops uncordon ops-worker
```

至少一副本应保持 Ready。drain 可能等待新副本调度/就绪；有资源不足或本地卷时需按事件诊断，不能强制绕过 PDB。为隔离变量，此参考应用无业务卷。

故障：在两副本健康时将 PDB minAvailable 改成 2，再尝试 drain，预期驱逐被预算阻挡并超时；保存拒绝证据，恢复 minAvailable=1 后完成维护，再 uncordon。PDB 只约束遵守 Eviction API 的自愿中断；直接 delete、硬断电、Deployment 滚动更新不受同样保护。

## DaemonSet 与节点故障

手写 busybox DaemonSet（sleep 3600），在 worker 节点各运行一个实例，说明控制平面污点为什么可能阻止其在控制平面运行。验证 drain 默认跳过 DaemonSet。

可选故障只对 ops-worker：`docker stop ops-worker`，观察 Node conditions、Pod 状态及业务副本变化，记录真实耗时；然后 `docker start ops-worker`。这与 drain 不同，PDB 不能阻止硬故障。不要对 labs 或 Docker Desktop 自身执行停止。结束确认节点 Ready 且已 uncordon。

## 备份与恢复桌面演练（必须，另约 60 分钟）

基于 Lab04 的临时测试数据库，手写备份/恢复命令清单：逻辑导出到节点外→在独立实例导入→核对行数与关键记录→记录 RPO/RTO。不要在现有唯一实例上覆盖恢复。只有查询到恢复数据才算验收，PVC 存在不等于备份。

控制平面层：口述 etcd 保存哪些对象，为什么 etcd 快照不包含 PV 中的业务文件；托管 K8s 与自建集群的备份/证书轮转/升级责任区别。此处不提供直接操作真实控制平面的快照恢复命令，使用官方对应版本 runbook 在独立环境演练。

## 最终面试与清理

提交维护前中后三份节点/副本/PDB 状态，解释 cordon、drain、uncordon；给出不可用时的止血、恢复、回滚条件。解释 API Server、etcd、scheduler、controller-manager、kubelet、CRI、CNI、CSI 各自故障影响。

确认无需要保留的数据后，只清理专用集群：`kind delete cluster --name ops`。再次确认 labs 仍存在。

参考：[Disruptions 与 PDB](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)。
