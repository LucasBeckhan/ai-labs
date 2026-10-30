# 哪些必须手写，哪些可以复用

代码server.py/domain.py、fixture、已有镜像允许直接复用；理解后再改。配置先看一次参考，合上后从空白写在自己的work/，允许查kubectl explain。不得把所有对象一股脑复制后只改名字。

| 阶段 | 必须写出的配置 | 必须解释的对应关系 | 验证 |
|---|---|---|---|
| 第一轮 | Deployment+Service | selector/template labels、80→8000、镜像/command | 集群内请求不是只看Pod |
| 第一轮 | startup/readiness/liveness | 暖机/业务就绪/进程存活三个信号 | 慢启动、依赖故障不误杀 |
| 第一轮 | ConfigMap env+volume | key、环境快照、文件路径、应用重读 | file/env不同步与重建 |
| 第一轮 | requests/limits | m/Mi单位、调度/运行时边界 | Pending与OOM证据 |
| 第一轮 | rollingUpdate | maxSurge/maxUnavailable/readiness | 坏版本不接流量、可回滚 |
| 第一轮 | PVC+Job/CronJob | claim/mount、重试、时区、Forbid、暂停 | 报告数值与归档恢复 |
| 第一轮 | Role+RoleBinding | SA/namespace/资源/动词/resourceNames | 允许1项、拒绝2项 |
| 第二轮 | Secret+安全上下文 | secretKeyRef与key、非root、写目录 | 假凭据引用与写权限 |
| 第二轮 | LimitRange+Quota | 默认值与namespace总预算 | API拒绝不是Pending |
| 第二轮 | HPA | requests分母、min/max、稳定窗口 | 指标可用才验收扩缩容 |
| 第二轮 | Ingress | class/host/path/后端Service | Controller与Host请求 |
| 第二轮 | StatefulSet+Headless | serviceName、稳定身份、每副本PVC | 数据存活与SC事件 |
| 独立环境 | NetworkPolicy | Pod/namespace选择器、双向允许、DNS | 真正允许/拒绝矩阵 |
| 独立环境 | affinity/tolerations | 标签选择与污点容忍 | 多节点调度结果 |
| 独立环境 | PDB+拓扑分散 | 可用预算与Eviction、hostname | drain与恢复 |
| 独立环境 | DaemonSet | 每节点实例、控制平面污点 | worker覆盖 |

建议每次从空白写的量控制在1–2个对象。提交时把每个关键字段用一句话解释；不必背整份API。

使用自己的对象名与专用练习namespace，不覆盖沙箱基线。若复用沙箱CM，练习对象须在同namespace且显式引用对应名称；创建自己的namespace则需复制自己的CM/SA依赖，K8s引用不会跨namespace自动找。
