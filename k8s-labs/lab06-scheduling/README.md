# Lab 06 — 调度控制：亲和性、污点容忍与 Pending 排障

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **2 小时** ｜ 前置：Lab 05 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q6

**学习循环：**
1. **读**（20min）：调度两阶段模型 + 污点/容忍语义方向（"亲和是 Pod 想去哪，污点是节点不让谁来"）
2. **跑**（40min）：**三种 Pending 的病历必须亲眼各看一次**（Events 原文）
3. **破坏练习**（30min，本章精华）：① 打污点后**故意不删**，去做别的事，等遇到全 Pending 时回来自己排障（真实事故体验）；② required 改 preferred 看差异
4. **验收自测**：① 调度两阶段？② Pending 四种病因与 Events 原文？③ 污点三个 effect？④ topologyKey 是什么？
5. **产出**：自己的"Pending 排查卡片"（现象 → 第一命令 → 修复）

## 学习目标

- 掌握调度器的两阶段模型（过滤 → 打分），Pod 的"落点"从此可解释
- 会用 nodeSelector / affinity / taint+toleration 把工作负载钉到该去的节点
- **掌握 Pending 的标准排查套路** —— 这是生产值班的基本功

## 核心问答

**Q1：调度器是怎么给 Pod 选节点的？**

> 参考答法：两阶段。**过滤（Predicates）**：剔除不满足硬条件的节点 —— 资源（requests 放不下）、端口冲突、亲和性/反亲和、污点未容忍、PV 无法挂载等；**打分（Priorities）**：对剩下的节点打分择优 —— 资源均衡、镜像位置（节点上已有镜像加分）、pod 反亲和软条件等。打完分选最高者绑定。调度只看 **requests**，不看实际用量 —— 这解释了"节点明明没跑满却调度不进去"的经典疑惑。

**Q2：污点（Taint）和容忍（Toleration）是什么？和亲和性有什么区别？**

> 参考答法：污点是**节点拒绝** Pod 的方式（NoSchedule 不再调度新的、PreferNoSchedule 尽量、NoExecute 还会驱逐已在运行的），容忍是 Pod 声明"我可以落在有这些污点的节点上"。语义方向相反：**亲和性是"Pod 想去哪"，污点是"节点不想让谁来"**。典型用途：GPU 节点打 `nvidia.com/gpu:NoSchedule` 污点，只有声明容忍 + 申请 GPU 资源的 Pod 才能上去，防止普通任务抢占 GPU 机器。

**Q3：一个 Pod 一直 Pending，你怎么排查？**

> 参考答法：`kubectl describe pod <name>` 看 **Events 段**，调度失败原因会明写：`Insufficient memory`（requests 太大）、`node(s) had untolerated taint`（污点）、`node(s) didn't match Pod's node affinity`（亲和性不满足）、`pod has unbound immediate PersistentVolumeClaims`（PVC 没绑上）。按事件对症：改 requests / 加容忍 / 改亲和 / 查 PV。没有事件就是调度器还没轮询到或上游卡住（镜像拉取看不上但容器没建）。

## 原理速讲

- `topologyKey`：反亲和的"拓扑域"单位 —— 用 `kubernetes.io/hostname` 表示"同一节点不能共存"，用 `topology.kubernetes.io/zone` 表示"同一可用区不能共存"。生产里三副本服务配 zone 级反亲和，一台机房挂了服务不倒。
- `required...` 是硬条件（不满足就 Pending），`preferred...` 是软条件（尽量满足，不满足照跑）。**生产上高可用部署 = preferred 反亲和 + required 留给强隔离场景**，避免单节点故障时硬条件把副本全部卡成 Pending。

## 动手实验

### 1. 给节点打标签，验证 nodeSelector

```bash
cd lab06-scheduling
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE workload=batch

kubectl apply -f manifests/scheduling-demo.yaml
kubectl get pod by-nodeselector     # 正常 Running
kubectl get pod -L workload         # -L 把节点 label 显示为一列，观察 Pod 都落在同一节点
```

### 2. 亲眼看见三种 Pending 的"病历"

```bash
kubectl describe pod greedy | grep -A 3 Events:
```

预期出现：

```
FailedScheduling: 0/1 nodes are available: 1 Insufficient memory.
```

```bash
kubectl describe pod anti-affinity-2 | grep -A 3 Events:
```

预期：`0/1 nodes are available: 1 node(s) didn't match pod anti-affinity rules.` —— 一个节点装不下"互斥"的两个副本。**所有 Pending 的根因都长这样，Events 就是调度器的自白书。**

> 修复练习：把 anti-affinity 的 `required` 改成 `preferred`（weight: 1）重新 apply，Pod 立刻 Running —— 体会硬/软条件的区别。

### 3. 污点：让节点"闭门谢客"，再为特权 Pod 开门

```bash
# 给节点加污点：没有容忍的 Pod 一律进不来
kubectl taint node $NODE gpu=true:NoSchedule

kubectl run no-toleration --image=busybox:1.36 -- sleep 3600
kubectl describe pod no-toleration | grep FailedScheduling
```

预期：`0/1 nodes are available: 1 node(s) had untolerated taint {gpu: true}.` —— 现有的 Pod 没被驱逐（NoSchedule 只管"新来的"），新建的全进不来。

```bash
# 声明了容忍的 Pod 就能进门（模拟"GPU 任务上 GPU 节点"）
kubectl run with-toleration --image=busybox:1.36 --overrides='
{"spec":{"tolerations":[{"key":"gpu","operator":"Equal","value":"true","effect":"NoSchedule"}],
"containers":[{"name":"app","image":"busybox:1.36","command":["sleep","3600"]}]}}' -- sleep 3600
kubectl get pod with-toleration    # Running

# overrides 里的 JSON 在声明三件事（等价于一个 YAML 的 spec 段）：
#   tolerations[0]  容忍 "gpu=true" 的 NoSchedule 污点 —— 能进门的前提
#   containers[0]   用 busybox 镜像，命令是 sleep 3600（挂着别退）
#   为什么用 --overrides？因为 kubectl run 没有直接设置容忍的旗标，JSON 注入最通用
```

### 4. 恢复现场（重要！）

```bash
kubectl taint node $NODE gpu=true:NoSchedule-    # 减号 = 移除污点
kubectl label node $NODE workload-               # 顺手把 label 也清了
kubectl delete pod no-toleration with-toleration
kubectl delete -f manifests/
```

预期 `kubectl describe node $NODE | grep Taints` 恢复为 `<none>`。**忘掉这步，后面所有实验全部 Pending** —— 这本身就是一次真实的排障经历。

## 观察与思考

1. 大数据视角：Spark on K8s 里 driver/executor Pod 的调度，正好可以用 affinity 做"driver 和 executor 打散到不同节点"，用 taint 做"大数据专用节点池"。你现在的平台里有哪些工作负载需要"专用节点池"？
2. `requests` 按什么调度、cgroup 按什么限制，两者不一致时会发生什么？（节点超卖：request 之和 > 节点实际内存，用量上来后互相挤兑 → 触发驱逐，QoS 决定谁走 —— 和 Lab 05 连起来了）
3. 一个节点上 Pod 越多越好吗？（调度器打分里的资源均衡项会倾向分散；另外镜像已存在节点的节点会加分 —— 大镜像的 Job 反复调度时能明显感觉到）

## 常见坑

- 实验里 taint 用完必须删，忘了删后面全部实验卡 Pending（现象就是 Q3 那句 `untolerated taint`）
- `operator: Exists` 不比较 value，直接容忍某 key 的所有污点 —— 模板里常用，但要清楚它很宽
- 单节点 kind 集群里"反亲和导致双副本互斥"很好演示；多节点生产集群里 preferred 反亲和才是常态
