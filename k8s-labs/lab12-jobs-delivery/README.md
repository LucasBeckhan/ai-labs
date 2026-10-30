# Job、CronJob 与声明式交付

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> 使用新版训练路线；每次实验提交 YAML、故障证据、恢复验证和面试复述，按 [统一验收](../CURRICULUM.md) 评分。参考清单用于核对，必须先手写。

## 手写任务（60–90 分钟）

先用 `kubectl explain job.spec` 查 backoffLimit、activeDeadlineSeconds、ttlSecondsAfterFinished，再从空白写出 reference.yaml 的 Job。业务要求：最多重试 2 次、总执行时间上限 90 秒、成功后保留 10 分钟便于采证。

```bash
kubectl --context kind-labs create namespace k8s-practice-12
kubectl --context kind-labs -n k8s-practice-12 apply -f reference.yaml
kubectl --context kind-labs -n k8s-practice-12 wait --for=condition=complete job/report --timeout=120s
kubectl --context kind-labs -n k8s-practice-12 logs job/report
```

预期看到 report complete 与 Complete condition；TTL 到期后对象可能已删除，及时采证。

## 故障任务

复制清单，改 Job 名为 report-failed，命令改为 `echo failed; exit 1`。记录 Pod 数、Job failed condition、Events；解释为何不会永远重试。修复不能直接修改已存在 Job 的 Pod 模板；创建新的作业名再验证成功。

独立写 CronJob，每两分钟启动一次任务，concurrencyPolicy=Forbid、startingDeadlineSeconds=60、successfulJobsHistoryLimit=1、failedJobsHistoryLimit=1。先令任务 sleep 180，观察上一轮未结束时不并发；采证后将 suspend=true。Forbid 只限制同一 CronJob，不能替代数据库幂等键或分布式锁。生产任务必须能处理重复触发与漏跑。

## Kustomize 发布练习

创建 work/base（Deployment+Service+kustomization.yaml）、work/overlays/dev（namespace、镜像标签或副本补丁）。base 使用 nginx:1.27，dev 使用 2 副本。先 `kubectl kustomize work/overlays/dev` 查看结果，再 server dry-run，最后 apply -k。保存生成的 YAML，验证 selector 和 labels 一致。不要把凭据写进 Git。

必须解释 Helm 的 chart/values/template 与 Kustomize patch 的差异，GitOps 的期望状态与现场手工改动如何冲突。部署工具不会替你保证数据库迁移兼容性。

## 验收

交付成功与失败 Job 的 conditions；CronJob 无并发证据；Kustomize 输出；用 3 分钟回答 Deployment、StatefulSet、DaemonSet、Job、CronJob 的选型，并给各自实际场景。DaemonSet 在 Lab14 验证。

清理：`kubectl --context kind-labs delete namespace k8s-practice-12`；CronJob 先 suspend，避免采证时又生成新任务。
