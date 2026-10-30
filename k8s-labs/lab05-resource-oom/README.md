# Lab 05 — 资源管理与 OOMKilled：requests/limits 的真实代价

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **2 小时** ｜ 前置：Lab 01 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q5 ｜ **本阶段最重要的一章**

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3 + 原理速讲的"QoS 判定规则"（逐条背）
2. **跑**（40min）：OOMKilled 复现（盯 exit 137）+ 三级 QoS 实测
3. **破坏练习**（20min）：① limit 从 128Mi 改 512Mi，看日志死在哪个数字（限额是硬顶）；② 造一个 requests==limits 的 Guaranteed Pod
4. **验收自测**：① request/limit 各控制什么？② QoS 三级判定（逐条）？③ 驱逐顺序？④ 137 的第一反应？⑤ JVM 堆为何是 limit 的 75%？
5. **产出**：给你一个陌生 Deployment YAML，能标出 QoS 等级与 OOM 风险点

## 学习目标

- 亲眼制造一次 **OOMKilled (exit 137)**，并学会从事件里定位
- 搞清 requests 与 limits 分别写进 cgroup 的什么，K8s 怎么用它们做调度和限制
- 掌握 QoS 三个等级的判定规则和**驱逐优先级**

## 核心问答

**Q1：requests 和 limits 有什么区别？**

> 参考答法：**requests 是调度的依据**（Scheduler 找"剩余 request 够用"的节点），是"保底"承诺，节点超卖时按 request 划分 CPU 时间片权重；**limits 是运行的硬顶**（内存写进 cgroup，超了就 OOMKilled；CPU 超了是节流 throttle，不会杀）。一句话：**request 决定你能占多少坑，memory limit 决定超过多少会死**。

**Q2：节点资源紧张时，先驱逐谁？**

> 参考答法：kubelet 按三级驱逐：先 BestEffort，再 Burstable 中实际用量超过 requests 的，最后才是 Guaranteed 或用量未超 requests 的 —— 即**"承诺兑现得越少、超额越多的越先走"**。同等级内部按"实际用量 / request"的比值排序。另外系统组件的 PriorityClass（system-node-critical）优先级最高不受此排序影响。

**Q3：exit code 137 是什么？**

> 参考答法：137 = 128 + 9（SIGKILL）。容器内存超过 cgroup limit，内核 OOM killer 直接杀进程。`kubectl describe pod` 的 Last State 里能看到 `Reason: OOMKilled`。Java/Flink/Spark 容器里出现 137，第一反应查堆外内存（direct memory、元空间、JVM 自身开销）是否吃掉了 limit 里留给非堆的部分 —— 这就是 Lab 01 里 MaxRAMPercentage=75 的由来。

## 原理速讲

- **内存 limits**：写入容器的 cgroup memory limit。进程分配内存触发内核记账超限 → 内核 OOM killer 杀容器主进程。**没有商量的余地，也不看应用是不是 GC 到一半。**
- **CPU limits**：cgroup cpu quota，超了会被**限流**（变慢）而不是被杀。所以生产上 CPU limit 经常不设或设很宽，内存 limit 必须精确。
- **QoS 判定**（判定规则要记牢）：
  - `Guaranteed`：每个容器 CPU 和内存都设了 request 且 == limit
  - `BestEffort`：所有容器都没设任何 resources
  - 其余一切情况 → `Burstable`

## 动手实验

### 1. 制造一次 OOMKilled

```bash
cd lab05-resource-oom
kubectl apply -f manifests/oom-demo.yaml

kubectl logs -f memory-hog
```

预期：日志一路 `allocated 10 MB ... allocated 130 MB`，然后在 ~130MB 处戛然而止（超过 128Mi 限额）。

```bash
kubectl get pod memory-hog
kubectl describe pod memory-hog | grep -A 6 "Last State"
```

预期输出：

```
NAME         READY   STATUS      RESTARTS
memory-hog   0/1     OOMKilled   0

Last State:   Terminated
  Reason:     OOMKilled
  Exit Code:  137
```

> 注意 `restartPolicy: Never` 让它死透了没重启；生产里默认 Always，你会看到 RESTARTS 一直涨 —— **RESTARTS 频繁 + exit 137 = 内存限额设小了或应用内存泄漏**，这是告警排查的固定套路。

### 2. 三种 QoS 长什么样

```bash
kubectl apply -f manifests/qos-demo.yaml
kubectl get pod qos-guaranteed qos-burstable qos-besteffort \
  -o custom-columns='NAME:.metadata.name,QOS:.status.qosClass'
```

预期：

```
NAME              QOS
qos-guaranteed    Guaranteed
qos-burstable     Burstable
qos-besteffort    BestEffort
```

### 3. 驱逐优先级的"思想实验"验证（低成本版）

单机 kind 上真做节点级驱逐需要制造节点内存压力，会拖慢你的 Mac，这里用只读方式理解：

```bash
kubectl get pod qos-besteffort -o jsonpath='{.status.qosClass}'; echo " ← 节点压力时第一个被杀"
kubectl describe node labs-control-plane | grep -A 8 "Allocated resources"
```

看 Allocated resources 段：**这里显示的是所有 Pod 的 requests 之和**，不是实际用量 —— 顺便理解了"request 是调度账本，limits 是运行账本"这句话。

> 想看真实用量：Lab 09 装好 metrics-server 之后，`kubectl top pod` 就是实际用量，两相对照理解更深。

### 清理

```bash
kubectl delete -f manifests/
```

## 观察与思考

1. 把 oom-demo 的 limit 改成 512Mi 再跑，死之前日志停在多少？（≈512MB 附近 —— 限额就是硬顶，多 1 字节都不行）
2. 为什么 CPU 超限不杀进程而内存超限要杀？（内存是"占用"型资源，超了系统就真的没有可用页了，必须回收；CPU 是"分时"资源，让一让就过去了）
3. 你的 Spark/Flink 作业迁到 K8s，executor 的 limit 该怎么定？（executor 内存 + JVM 开销 + 堆外 + 网络缓冲，Spark 配置里 `spark.executor.memoryOverhead` 就是为这个设计的 —— 把 YARN 时代的经验翻译过来即可）

## 常见坑

- OOMKilled 后 `logs` 可能为空 —— 进程还没来得及刷日志就被杀了；看 `describe` 的 exit code 而不是猜
- `limits.memory` 里别忘了非堆内存：Java 应用堆设 limit 的 75%，留 25% 是经验起点，不是教条
- kind 单节点上 BestEffort Pod 无害，但别在本机生产 Docker 里跑无限额容器 —— 吃光 8GB 会卡死你的 Mac
