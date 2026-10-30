# Kubernetes实战：从大数据架构到云网安平台交付

结合中企通信公开的云、网络与信息安全服务方向，以及你提到的网络监控、安全周报、数据治理工作设计案例。**全部使用虚构数据，不代表公司真实接口、架构或SLA。** [公开业务依据](https://www.china-entercom.com/Product-Services-Summary)

先走 **[6次快速实战](business/FAST-TRACK.md)**，用同一个模拟业务练会部署、发布、排障、资源、任务和恢复；再按 [14章知识路线](CURRICULUM.md) 补齐机制。业务沙箱有 [30个具体任务](business/DRILLS.md)，前9题可自动注入故障，其余手写或手动操作。

## 先准备什么

| 环境 | 检查/用途 |
|---|---|
| Docker Desktop运行 | docker version；kind节点与镜像所在环境 |
| kind | kind version；现有labs可复用 |
| kubectl | 尽量与集群版本匹配，遵循官方version skew policy |
| Python3 | 新业务工具仅用标准库，不需要模型/云账户/额外pip依赖 |
| 内存 | 基础主线约需几个小Pod；多节点、Spark、监控栈另预留资源，不同时启动全部章节 |

复现实验固定节点镜像v1.31.4，不代表推荐用于生产新建集群。[kubectl版本兼容说明](https://kubernetes.io/releases/version-skew-policy/)

Lab01前四步只需Docker；不必先创建集群或准备所有镜像。先构建，基础镜像下载失败再处理网络/镜像缓存。`build-spark-image.sh`只在Lab10需要Spark替代镜像时使用。

## 开始业务主线

```bash
cd /Users/hp/Documents/ai-labs/k8s-labs
kind get clusters
```

已有labs时不重建；没有时执行：

```bash
kind create cluster --name labs --config kind-config.yaml
```

Python镜像在节点不可用时，再运行统一准备脚本（会准备所有原实验镜像，耗时可能较长）：

```bash
bash hack/prepare-images.sh
```

它依次拉取、恢复标准标签、导入labs；失败后仍可能继续，检查FAIL/load失败。kind节点与Docker使用独立镜像库，Docker已有镜像不等于节点已有。

然后：

```bash
python3 business/labctl.py up
python3 business/labctl.py verify
```

预期两副本Ready，集群内查询成功，原始告警3条、去重2条。之后按 [沙箱说明](business/README.md) 打开页面与做题。无需新装模型、Kafka、Doris或云账户，也不改现有各章对象。

## 每次实战怎么学

1. 先跑健康基线，说明业务输入/输出及哪些数据为模拟。
2. 对照一次参考后合上，从空白写指定配置；公共业务代码与fixture允许复用。
3. 每次只注入一个故障，记录用户影响、状态/日志两条证据。
4. 做自己的最小修复，用Service实际请求、任务数字或恢复内容验收。
5. 保存配置diff与复盘，最后核对恢复。不要用recover、删集群代替诊断。

用 [手写清单](business/WRITE-CHECKLIST.md) 自查，按 [故障记录模板](INCIDENT-TEMPLATE.md) 留证。只看到Running或Job Complete不算过关。

## 14章业务映射

| 章 | 原理参考 | 业务实战入口 |
|---|---|---|
| 01 | [容器与镜像](lab01-container-basics/README.md) | [交付监控采集程序](lab01-container-basics/BUSINESS-PRACTICE.md) |
| 02 | [Pod生命周期](lab02-pod-lifecycle/README.md) | [API启动、就绪、退出](lab02-pod-lifecycle/BUSINESS-PRACTICE.md) |
| 03 | [Deployment发布](lab03-deployment-rollout/README.md) | [监控平台发布与止血](lab03-deployment-rollout/BUSINESS-PRACTICE.md) |
| 04 | [StatefulSet与存储](lab04-statefulset-storage/README.md) | [报告归档与恢复](lab04-statefulset-storage/BUSINESS-PRACTICE.md) |
| 05 | [资源与OOM](lab05-resource-oom/README.md) | [消费者内存边界](lab05-resource-oom/BUSINESS-PRACTICE.md) |
| 06 | [调度](lab06-scheduling/README.md) | [资源池与采集节点](lab06-scheduling/BUSINESS-PRACTICE.md) |
| 07 | [网络入口](lab07-network-ingress/README.md) | [监控门户访问链路](lab07-network-ingress/BUSINESS-PRACTICE.md) |
| 08 | [排障](lab08-troubleshooting/README.md) | [值班故障轮训](lab08-troubleshooting/BUSINESS-PRACTICE.md) |
| 09 | [HPA](lab09-hpa-autoscaling/README.md) | [查询高峰容量](lab09-hpa-autoscaling/BUSINESS-PRACTICE.md) |
| 10 | [Spark与监控](lab10-spark-monitoring/README.md) | [数据作业与业务指标](lab10-spark-monitoring/BUSINESS-PRACTICE.md) |
| 11 | [配置与安全](lab11-config-security/README.md) | [数据配置与授权](lab11-config-security/BUSINESS-PRACTICE.md) |
| 12 | [Job与交付](lab12-jobs-delivery/README.md) | [云安全周报任务](lab12-jobs-delivery/BUSINESS-PRACTICE.md) |
| 13 | [DNS与网络策略](lab13-network-policy/README.md) | [访问隔离](lab13-network-policy/BUSINESS-PRACTICE.md) |
| 14 | [节点维护与恢复](lab14-node-recovery/README.md) | [维护窗口与采集DaemonSet](lab14-node-recovery/BUSINESS-PRACTICE.md) |

原README用于原理与基础示例，新BUSINESS-PRACTICE映射到统一任务册；旧PRACTICE保留作第二轮考核。无需把同一题机械做三遍。

## 环境边界、清理与验证

沙箱固定context=kind-labs、namespace=cec-k8s-practice并检查所有权；clean会删除其练习PVC与模拟归档，先备份需要的内容，不删kind集群。

默认kind不能执行NetworkPolicy；多节点维护使用独立ops集群；单机双副本不代表跨机房高可用。API无真实鉴权，固定租户只是数据过滤演示。真实网络变更、客户报告发送、SOC封禁均不在训练动作中。

本次新增内容的实际验证范围与限制见 [验证记录](business/VALIDATION.md)；原章节历史“已实测”说明不代表全部新业务题已执行。

其他模块：[Agent业务训练](../agent-labs/CURRICULUM.md)、[LLMOps](../llmops-labs/README.md)、[K8s面试题](../interview-prep/01-kubernetes.md)、[术语速查](GLOSSARY.md)。
