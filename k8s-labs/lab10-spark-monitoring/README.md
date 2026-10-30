# Lab 10 — 毕业项目：Spark on K8s + Prometheus 监控

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


把前 9 个实验的能力拧成一股绳：**RBAC、资源限制、Pod 生命周期、服务发现、指标采集**全部登场。这个实验做完，"把大数据平台搬到 K8s"这件事你就有了完整的第一手经验 —— 也拥有了一个可以持续扩展的云原生数据平台骨架。

## 📖 本章学习指导

> 建议时长 **4 小时（分两次）** ｜ 前置：Lab 01-09 全部 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q14-Q15

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3（Q1 的 executor 启动机制是源码级结论，背熟）
2. **跑**（90min）：RBAC → 提交 SparkPi（**亲眼看 driver/executor Pod 生灭**，`Pi is roughly` 出现才算过）→ Part B 监控栈
3. **破坏练习**（30min）：① 删掉 Role 的 patch 权限重新提交，亲眼看 Forbidden 再修复；② 改错 metrics-app 注解端口，看 Prometheus target 变 down
4. **验收自测**：① vs YARN 架构差异？② executor 真实启动方式？③ RBAC 为何要 patch？④ 注解发现原理？
5. **产出**：SparkPi 结果 + Prometheus target up 截图 + Grafana 曲线——你的 K8s 实物证据

## 学习目标

- 理解 **Spark on K8s 的运行架构**（driver/executor 都是 Pod），能和 YARN 模式对比
- 亲手用 cluster 模式提交 SparkPi，观察 driver/executor Pod 的生灭
- 理解 Spark 需要什么 RBAC 权限，为什么（"组件也是 K8s API 客户端"这一课）
- 搭一套最小 Prometheus + Grafana，理解**注解发现**这种 K8s 生态的标准监控模式
- 了解 GPU 调度原理（概念层，本机无 GPU）

## 核心问答

**Q1：Spark on K8s 和 Spark on YARN 的架构区别？**

> 参考答法：YARN 里 ApplicationMaster/Container 由 ResourceManager 统一调度，资源单位是 Container；K8s 模式里 **driver 和 executor 直接是 Pod**，由 K8s 调度器分配，Spark 通过 K8s API 创建它们（driver 以 SA 身份调 API —— 所以要 RBAC）。一个值得说的细节（本实验源码级验证过）：**executor 容器的启动命令不是 spark-submit**，Pod args 只有 `["executor"]`，真正的进程由镜像 entrypoint 拉起 —— `java ... KubernetesExecutorBackend --driver-url $SPARK_DRIVER_URL ...`，driver URL、executor ID、内存核数全部由 driver 以**环境变量**注入。优势：① 资源粒度更细（Pod 级 limits/requests 直接生效）；② 和云原生生态打通（日志、监控、镜像统一）；③ 弹性伸缩更自然。代价：① 需要管理镜像与 RBAC；② 动态资源分配（external shuffle service）在 K8s 上实现方式不同，shuffle 迁移要靠 Spark 3.4+ 的 shuffle tracking。**一句话：YARN 的"容器"换成了 K8s 的"Pod"，调度权交给了 kube-scheduler。**

**Q2：Spark on K8s 需要什么 RBAC？为什么？**

> 参考答法：cluster 模式下 driver 是"你的代理人"，要创建/删除 executor Pod、创建并**更新** driver Service，需要对应 Role（pods 和 services 的 get/list/watch/create/update/patch/delete）。**patch 权限最容易漏** —— 本实验实测：只给 create/delete 时，spark-submit 创建 driver Service 后 PATCH 失败，报 `cannot patch resource "services"`。**给 SA 最小权限**是原则 —— 实验里用 Role（namespace 级）而不是 ClusterRole。

**Q3：K8s 里的监控体系是怎样的？**

> 参考答法：三层。**kubelet/cAdvisor** 暴露容器级指标（metrics-server 消费它做 HPA，Lab 09）；**Prometheus** 拉取聚合：通过 `kubernetes_sd_configs` 服务发现自动找到目标（本实验用注解发现，生产更多用 ServiceMonitor/Prometheus Operator），配 RBAC 才能 list Pod；**Grafana** 消费 Prometheus 做可视化。大数据组件的 Prometheus 指标都是标配：Spark 有 `metrics.properties` + Prometheus servlet，Flink 有内置 Metrics Reporter。

## 动手实验

### Part A：Spark on K8s

#### 1. 准备 RBAC 和镜像

```bash
cd lab10-spark-monitoring
kubectl apply -f spark/spark-rbac.yaml

# 镜像二选一：
# A) 网络可达 Docker Hub 时直接拉（约 700MB）
docker pull apache/spark:v3.5.5
# B) 网络受限时本地构建等价镜像（官方 entrypoint + tini，已验证）
../hack/build-spark-image.sh

kind load docker-image apache/spark:v3.5.5 --name labs
```

> B 路径的构建脚本会：从华为云镜像站下载 Spark 3.5.5 二进制包 → 用包内自带的官方 `entrypoint.sh` + tini 构建 → 等价于官方镜像。生产上不需要 `kind load` —— 镜像在仓库里，节点直接拉；kind 是"节点容器共享你 Mac 镜像"的特例。

#### 2. cluster 模式提交 SparkPi

```bash
kubectl run spark-submit --restart=Never \
  --image=apache/spark:v3.5.5 \
  --overrides='{"spec":{"serviceAccountName":"spark"}}' \
  -- spark-submit \
    --master k8s://https://kubernetes.default.svc \
    --deploy-mode cluster \
    --name spark-pi \
    --class org.apache.spark.examples.SparkPi \
    --conf spark.executor.instances=2 \
    --conf spark.executor.memory=512m \
    --conf spark.executor.cores=1 \
    --conf spark.kubernetes.container.image=apache/spark:v3.5.5 \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    local:///opt/spark/examples/jars/spark-examples_2.12-3.5.5.jar 100

kubectl get pods -w     # 观察：先出现 spark-pi-xxx-driver，再出现 2 个 exec-N
```

命令很长，逐参数拆解（建议对照着读一遍再执行）：

| 参数 | 作用 |
|---|---|
| `kubectl run spark-submit --restart=Never --image=...` | 起一个一次性 Pod 作为"提交客户端"（跑 spark-submit 进程） |
| `--overrides='{"spec":{"serviceAccountName":"spark"}}'` | 给这个 Pod 挂 spark 服务账号（kubectl 1.31+ 移除了 --serviceaccount 旗标，只能用 JSON 注入） |
| `-- spark-submit ...` | `--` 之后是容器里真正执行的命令 |
| `--master k8s://https://kubernetes.default.svc` | 告诉 spark-submit：K8s API 就在集群内这个地址 |
| `--deploy-mode cluster` | driver 以独立 Pod 运行（对比 client 模式：driver 在提交端） |
| `--name spark-pi` | 应用名，driver Pod 会叫 spark-pi-xxx-driver |
| `--class ...SparkPi` | 要执行的主类（官方示例里的圆周率计算） |
| `spark.executor.instances/memory/cores` | 2 个 executor、各 512MB 内存 1 核（会转成 Pod 的 requests/limits） |
| `spark.kubernetes.container.image` | driver/executor Pod 用哪个镜像 |
| `authenticate.driver.serviceAccountName=spark` | driver Pod 用 spark 账号去创建 executor（RBAC 的意义所在） |
| `local:///opt/spark/examples/jars/...jar 100` | 任务 jar（local:// 表示镜像内路径）+ 迭代次数 100 |

> 注意用 `--overrides` 而不是 `--serviceaccount=spark`：kubectl v1.31 起已移除该旗标（本机 kubectl 1.36 实测）。

预期时序：`spark-submit` Pod 创建 **driver Pod**（cluster 模式下 driver 独立成 Pod）→ driver 通过 RBAC 创建 **2 个 executor Pod** → 计算完成 → driver/executor 均 Completed（executor Pod 保留为 Completed 状态，几分钟内被 driver 清理）。

```bash
DRIVER=$(kubectl get pods -o name | grep driver)
kubectl logs $DRIVER | grep "Pi is roughly"
```

预期（实测）：`Pi is roughly 3.1422527142252714`（迭代 100 次，约 15~30 秒）。**亲手看到这行 = Spark on K8s 跑通了。**

#### 3. 观察 Pod 的资源形态

```bash
kubectl get pod -o wide | grep spark
# driver/executor 消失后（Completed/已清理），回看提交日志：
kubectl logs spark-submit | grep -E "executor|driver" | head -5
```

> 对照思考：executor Pod 的资源限制来自 `spark.executor.memory/cores` → Spark 翻译成 Pod 的 requests/limits（还自动加上 overhead）。你在 YARN 时代调的 executor 内存三件套，在这里原样适用，只是执行者从 NodeManager 换成了 kubelet + cgroup（Lab 05 的知识直接复用）。

### Part B：Prometheus + Grafana 监控

#### 4. 部署监控栈和一个带指标的应用

```bash
kubectl apply -f manifests/
kubectl get pods -w    # 等 metrics-app、prometheus、grafana 全部 Running
```

#### 5. 验证"注解发现"

```bash
kubectl port-forward deploy/prometheus 9090:9090 &
# 浏览器打开 http://localhost:9090 → Status → Targets
```

预期：`kubernetes-pods` job 下有一个 `UP` 的目标（metrics-app）—— **Prometheus 自动找到了它，因为它有 `prometheus.io/scrape: "true"` 注解**。查询框输入：

```promql
demo_requests_total
```

能看到递增的计数器。再加一个按 Pod 维度的容器内存查询：

```promql
sum by (pod) (container_memory_working_set_bytes{namespace="default"})
```

> 这条 PromQL 就是"看每个 Pod 实际用多少内存" —— 和 Lab 05 的 limits 对照，你会立刻明白哪些 Pod 逼近限额。

#### 6. Grafana 出图

```bash
kubectl port-forward deploy/grafana 3000:3000 &
# 浏览器 http://localhost:3000，账号 admin/admin
```

步骤：Connections → Data sources → Add → **Prometheus** → URL 填 `http://prometheus:9090`（集群内 Service DNS，Lab 07 的知识）→ Save & Test → 建一个 Panel，查询 `demo_requests_total`，看曲线。

#### 7. 清理

```bash
kill %1 %2 2>/dev/null
kubectl delete -f manifests/
kubectl delete -f spark/spark-rbac.yaml
```

## 观察与思考

1. **GPU 调度是怎么回事？**（本机没有 GPU，概念必须会：节点装 NVIDIA device plugin DaemonSet 后，GPU 成为一种可调度的扩展资源，Pod 里 `resources.limits: nvidia.com/gpu: 1` 申请；节点打污点防普通任务抢占（Lab 06 知识）；整卡浪费时可配 **time-slicing** 共享，但要自担隔离弱的风险 —— 这是推理资源管理的核心话题）
2. 为什么生产常用 **Prometheus Operator + ServiceMonitor** 而不是注解发现？（Operator 把"监控配置"变成 CRD —— 写 YAML 声明"监控这些 Service"，不需要手写 relabel 规则，团队协作不易乱；本实验的注解方案是理解其原理的最小底座）
3. **MLOps 地图**：现在你能把这条链路看完整了 —— Git 提交训练代码 → CI 构建镜像（Lab 01）→ K8s Job/GPU 节点训练（Lab 06）→ 模型推理由 KServe/Triton 承载（Pod + Service + Ingress，Lab 07）→ Prometheus 监控（本实验）→ HPA/KEDA 伸缩（Lab 09）。**这就是机器学习平台的标准骨架，缺哪块补哪块。**

## 常见坑

- 本实验本地构建镜像时踩过三个真实的坑，都值得记住：① **镜像里 `$SPARK_HOME` 必须 chown 给运行用户**（cluster 模式下 Spark 把 `local:` 资源拷贝到 `$SPARK_HOME` 下，否则 driver 报 `AccessDeniedException`）；② **executor 进程不是 spark-submit**（entrypoint 按 env 拉起 KubernetesExecutorBackend，见 Q1）；③ 官方镜像不把 spark-submit 放进 PATH（要么写全路径，要么自己加 ENV）
- driver Pod 卡在 Pending / executor 一个都不出来：十有八九是 RBAC 没生效（尤其 patch 权限）或 SA 名字写错，`kubectl get role,rolebinding` 核对；用 `kubectl logs spark-submit` 看 fabric8 的报错原文
- Prometheus Targets 页面空：检查 SA 是否绑定（view ClusterRole）、metrics-app 注解是否在 Pod 模板（Deployment 的 `template.metadata.annotations`，不是 Deployment 自己的）
- **Target 显示 down 且报 `non-compliant scrape target sending blank Content-Type`**：Prometheus v3 严格要求 /metrics 端点返回 `Content-Type` 头，自研导出器必须带 `Content-Type: text/plain; version=0.0.4`（v2 时代不写也能抓，升级 v3 后大批自研 exporter 一起"阵亡"是真实的事故场景）
- port-forward 是阻塞命令，开后台（`&`）或另开终端；结束实验记得 `kill`
- Grafana 数据源 URL 必须用 `http://prometheus:9090`（Service DNS），写成 localhost 是最常见的错误 —— Prometheus 在另一个 Pod 里
