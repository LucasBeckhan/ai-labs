# Lab 09 — HPA 自动扩缩容：让集群自己应对流量

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **2.5 小时** ｜ 前置：Lab 05 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q13

**学习循环：**
1. **读**（20min）：HPA 算法公式 + "分母是 requests 不是 limits"（本章最易错点）
2. **跑**（50min）：metrics-server 安装 → 压测看 2→8 扩容 → 撤压看**稳定窗口后回落**（亲眼见"缩容慢半拍"）
3. **破坏练习**（20min）：① requests.cpu 100m 改 400m，看 HPA 变"迟钝"（分母变大的代价）；② 删掉 requests 看 TARGETS 变 unknown
4. **验收自测**：① HPA 算法？② 分母为什么是 requests？③ 缩容为什么有稳定窗口？④ Flink 为什么不能简单 HPA？⑤ metrics-server 挂了 HPA 会怎样？
5. **产出**：扩容与缩容各一张时间线记录（TARGETS/REPLICAS 随时间）

## 学习目标

- 装上 metrics-server，打通"容器指标 → K8s API"这条链路
- 亲手触发 HPA 扩容和缩容，理解它的算法和节奏控制
- 知道 HPA 的边界在哪，什么场景该换 KEDA

## 核心问答

**Q1：HPA 的工作原理？**

> 参考答法：HPA 控制器每 15 秒（`--horizontal-pod-autoscaler-sync-period`）从 **metrics API**（`metrics.k8s.io`，由 metrics-server 提供）读取目标 Pod 的 CPU/内存用量，计算期望副本数：`期望 = ceil(当前副本数 × 实际值 / 目标值)`。例如 2 个副本 CPU 80%、目标 50% → `ceil(2 × 80/50) = 4`。它只管**水平**改副本数，不碰资源限额；和 Cluster Autoscaler（加减节点）、VPA（改资源配置）分层配合。**注意：CPU 利用率的分母是 requests，不是 limits** —— 所以 requests 设得虚高，HPA 会"迟钝"。

**Q2：为什么扩容快、缩容慢？**

> 参考答法：防止流量抖动引发震荡（thrashing）。HPA 的 `behavior` 可分别配置扩/缩容的 `stabilizationWindowSeconds`（观察窗口）和每分钟最大变化率。默认缩容窗口 5 分钟：流量瞬时跌落不立刻砍副本，等确认是持续下降才收。**生产配置经验：扩容激进（业务优先），缩容保守（省钱不救急）**。

**Q3：HPA 搞不定的场景怎么办？**

> 参考答法：HPA 只支持 CPU/内存（以及少数自定义指标），**不适合按队列积压伸缩** —— Flink/Kafka 消费积压、Flink 反压这类"指标在业务系统里"的场景用 **KEDA**：它从 Kafka lag、Redis 长度等外部指标取数，同样驱动 Deployment/Job 伸缩（内部就是包装了 HPA + 外部 metrics adapter）。批处理类（定时大任务、离线跑批）用 CronJob 或 KEDA 的 cron scaler 更自然。

## 动手实验

### 1. 安装 metrics-server（kind 里必须关证书校验）

> 清单已 vendor 到本地（`manifests/metrics-server.yaml`，源自官方 v0.7.2 components.yaml），不依赖外网；镜像已在准备阶段 `kind load` 进集群。

```bash
kubectl apply -f manifests/metrics-server.yaml
kubectl -n kube-system patch deployment metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

kubectl -n kube-system rollout status deploy/metrics-server --timeout=180s
kubectl top nodes    # 有数据即安装成功（首次约需 1 分钟采集）
```

### 2. 部署应用 + HPA

```bash
cd lab09-hpa-autoscaling
kubectl apply -f manifests/app.yaml
kubectl get hpa calc
```

预期（暂无压测）：`TARGETS 0%/50%`（或 `<unknown>` 一两分钟后变 0%），`REPLICAS 2`。

### 3. 加压，看扩容

```bash
kubectl apply -f manifests/loadgen.yaml
kubectl get hpa calc -w
```

预期时间线（快的话 1 分钟内）：

```
NAME   TARGETS   REPLICAS   AGE
calc   160%/50%  2          3m     ← 4 个压测副本把 2 个 calc 全打满
calc   88%/50%   4          3m     ← ceil(2×160/50)=7？一次扩到 7，逐步逼近
calc   61%/50%   7          4m
calc   49%/50%   8          5m     ← maxReplicas=8 兜住
```

> 数字对不上算法不要慌：HPA 是连续多轮的，每轮读取的是"全部副本的平均值"，且单轮最多 ±100%/10% 变化 —— **看趋势对齐即可**。

```bash
kubectl get pods -l app=calc | wc -l    # 验证副本真的变多了
```

### 4. 撤压，看缩容（慢半拍是特性）

```bash
kubectl delete -f manifests/loadgen.yaml
kubectl get hpa calc -w    # 继续挂着观察
```

预期（实测时间线）：TARGETS 一两分钟内掉到 1%/50%，但 **REPLICAS 顶着 60 秒稳定窗口保持 8 不动**，窗口确认后一次性回落到 minReplicas=2（默认缩容策略允许一步到位；想分批回落可给 `behavior.scaleDown` 加 `policies: [{type: Percent, value: 25, periodSeconds: 60}]`）—— 这就是缩容稳定窗口，故意不让你"过山车"。

### 清理

```bash
kubectl delete -f manifests/app.yaml
# 注意：metrics-server.yaml 也在 manifests/ 里，`kubectl delete -f manifests/` 会把它一起删掉
# （删了也没关系，下次重新 apply 即可；重装后要等 1 分钟指标才可用）
```

## 观察与思考

1. 把 calc 的 `requests.cpu` 从 100m 改成 400m，HPA 的 TARGETS 会怎么变？（同样负载下利用率变成 1/4，更难触发扩容 —— **requests 是 HPA 的刻度尺**，再次强调 Q1 的分母问题）
2. 你的 Flink 作业在 K8s 上该怎么伸缩？（Flink 作业不是无状态 HTTP 服务，**不能简单 HPA** —— 要靠 JobManager 的 rescale/savepoint 机制，或 KEDA 按 Kafka lag 触发 + 作业级重启恢复。这是"把 YARN 经验翻译成 K8s 语言"最典型的差异点，值得深入理解）
3. metrics-server 的数据从哪来？（各节点 kubelet 内嵌的 cAdvisor 暴露容器指标 → metrics-server 聚合 → metrics API。它只存最近几分钟，**不是监控系统** —— 历史曲线要靠 Lab 10 的 Prometheus）

## 常见坑

- `kubectl top` 报 `error: Metrics API not available`：metrics-server 还没 ready，等 1 分钟再看
- `<unknown>/50%` 卡住不变成 0%：检查 Pod 是否设置了 `requests.cpu`（没设 requests 的容器无法计算利用率）
- 压测副本的 CPU limit（200m×4）要明显大于被压服务的总 request（100m×2），否则打不满
