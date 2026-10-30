# 配置更新、权限与租户隔离

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> 使用新版训练路线；每次实验提交 YAML、故障证据、恢复验证和面试复述，按 [统一验收](../CURRICULUM.md) 评分。参考清单用于核对，必须先手写。

## 目标与必须手写的字段

从空白写 ConfigMap、Secret、Pod、ServiceAccount、Role、RoleBinding、LimitRange、ResourceQuota。必须解释 configMapRef、secretKeyRef、volumes、volumeMounts、subjects、roleRef；不背整份 YAML。Secret 的 base64 不是加密，勿使用真实密码；本练习文件中的值都是假数据。

## 运行与观察（约 90 分钟）

在本章目录执行：

```bash
kubectl --context kind-labs create namespace k8s-practice-11
kubectl --context kind-labs -n k8s-practice-11 apply -f reference.yaml
kubectl --context kind-labs -n k8s-practice-11 wait --for=condition=Ready pod/config-reader --timeout=120s
kubectl --context kind-labs -n k8s-practice-11 logs config-reader
kubectl --context kind-labs -n k8s-practice-11 exec config-reader -- cat /config/MODE
```

预期启动日志为 `env=blue`，文件内容为 `blue`。先尝试独立手写，再使用 reference.yaml 对照。

将 ConfigMap 的 MODE 改为 green，重新 apply：反复读取 `/config/MODE`，直到看到 green，记录耗时；不能假定固定一分钟。`logs` 的启动输出仍是 blue，启动时注入的环境变量不会随之更新。删除并按清单重建 Pod 后日志变 green。已有挂载文件改变不等于程序会重载，应用要主动重新读取；subPath 挂载不会接收这些更新。

## 最小权限练习

```bash
kubectl --context kind-labs auth can-i get configmaps --as=system:serviceaccount:k8s-practice-11:reader -n k8s-practice-11
kubectl --context kind-labs auth can-i get secrets --as=system:serviceaccount:k8s-practice-11:reader -n k8s-practice-11
kubectl --context kind-labs auth can-i delete pods --as=system:serviceaccount:k8s-practice-11:reader -n k8s-practice-11
```

期望 yes/no/no。这些命令从管理员视角模拟身份，并不验证容器内 token 调用。Pod 设置了 `automountServiceAccountToken: false`；应用不访问 API 时无需注入 token。

故障：在自己写的 RoleBinding 中改错 subject.name，观察原 reader 的允许结果变 no，再恢复。不要修改集群管理员授权。

## 资源隔离与安全练习

手写 LimitRange（默认 requests CPU 50m、内存 32Mi，limits CPU 200m、内存 64Mi）与 ResourceQuota（requests.cpu=500m、requests.memory=256Mi、limits.cpu=1、limits.memory=512Mi、pods=4），部署在本章 namespace。分别创建未写 resources 的 Pod、写 requests.cpu=2 的 Pod：前者由 LimitRange 补默认值，后者因配额拒绝（通常 API Forbidden，而非已创建的 Pod Pending）。保存原始拒绝输出，删除练习对象释放配额。

手写受限 Pod 安全配置：runAsNonRoot、allowPrivilegeEscalation=false、capabilities.drop=[ALL]、seccompProfile.type=RuntimeDefault。使用支持非 root 的镜像或为 busybox 设置非零 UID，验证 `id`。readOnlyRootFilesystem 需要同时考虑应用写目录和 emptyDir。不要不加分析地套到需要绑定低端口或写系统目录的镜像。

## 验收与面试

提交三种配置传递方式（环境变量、目录挂载、subPath）的更新行为对照；提交三条 can-i 结果和配额拒绝证据。口述认证、授权、准入的区别；Secret 如何结合静态加密、RBAC、外部密钥服务保护。namespace 本身不是完整安全边界。

清理：`kubectl --context kind-labs delete namespace k8s-practice-11`，只删除本章专用 namespace。
