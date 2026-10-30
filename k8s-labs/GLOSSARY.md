# K8s 术语表（按实验出现顺序）

> 小白建议：先扫一遍混个脸熟，做实验时遇到不懂的词回来查。每条一句话，只讲"它是什么/为什么需要"。

## 容器基础（Lab 01）
- **镜像（Image）**：应用 + 运行环境的只读打包文件，容器是它的运行实例
- **分层（Layer）**：镜像由多层叠成，层可缓存复用 —— Dockerfile 每条指令生成一层
- **多阶段构建（Multi-stage build）**：编译用一个"大"镜像，运行只用装了产物的"小"镜像
- **namespace**：Linux 内核的"视图隔离"，让容器以为自己独占一套系统资源
- **cgroup**：Linux 内核的"资源限额"，限制容器能用多少 CPU/内存 —— K8s limits 的底层就是它
- **非 root 用户**：镜像里用普通用户身份运行进程，缩小被攻击后的影响面

## Pod 与生命周期（Lab 02）
- **Pod**：K8s 最小部署单元，包含一个或多个共享网络/存储的容器
- **探针（Probe）**：kubelet 定期对容器做健康检查的机制
- **startupProbe**：启动探针，通过之前其他探针不生效 —— 给慢启动应用留时间
- **readinessProbe**：就绪探针，失败就从 Service 摘除（不接流量，但不重启）
- **livenessProbe**：存活探针，失败就重启容器
- **SIGTERM / SIGKILL**：礼貌的终止信号 / 强杀信号；宽限期（terminationGracePeriodSeconds）是两者之间的倒计时
- **preStop 钩子**：容器收到终止信号前执行的脚本，常用来"等流量摘除完再退"

## 工作负载（Lab 03）
- **Deployment**：管理无状态应用副本与滚动更新的控制器
- **ReplicaSet**：维持 Pod 副本数恒定的控制器，Deployment 的下层
- **滚动更新（RollingUpdate）**：新版本逐个替换旧版本，全程服务可用
- **maxSurge / maxUnavailable**：更新时最多多出/最多缺少的 Pod 数 —— 容量与速度的平衡
- **金丝雀发布（Canary）**：先让小比例流量用新版本，观察无异常再全量

## 存储与有状态（Lab 04）
- **PV / PVC**：实际存储资源 / 用户对存储的申请单，二者绑定后使用
- **StorageClass**：存储"模板"，按 PVC 自动创建 PV（动态供应）
- **StatefulSet**：给 Pod 稳定序号身份（mysql-0/1）和独立存储的控制器，跑数据库用
- **Headless Service**：不做负载均衡的 Service，DNS 直接解析到每个 Pod —— StatefulSet 标配

## 资源与 QoS（Lab 05）
- **requests**：调度的依据（节点必须"装得下"），也是资源分配的保底
- **limits**：运行时的硬顶；内存超了 OOMKilled（exit 137），CPU 超了只是变慢
- **QoS**：Pod 的资源保障等级 —— Guaranteed（request==limit）> Burstable > BestEffort
- **驱逐（Eviction）**：节点资源紧张时 kubelet 按等级从低到高杀 Pod

## 调度（Lab 06）
- **nodeSelector / affinity**：Pod 指定"想去哪些节点"的规则
- **污点（Taint）与容忍（Toleration）**：节点拒绝 Pod 的方式 / Pod 声明"我能接受这种拒绝"
- **Pending**：Pod 已创建但没有节点能容纳它 —— 排障入口是 describe 的 Events

## 网络（Lab 07）
- **Service**：一组 Pod 的稳定访问入口（虚拟 IP + 负载均衡）
- **Endpoints**：Service 背后真实的 Pod IP 列表（selector 圈出来的）
- **ClusterIP / NodePort / LoadBalancer**：三种暴露方式，由内到外
- **Ingress**：七层（HTTP）入口，按域名/路径把流量路由到不同 Service
- **CoreDNS**：集群内 DNS，`svc名.命名空间.svc.cluster.local` 格式

## 排障（Lab 08）
- **CrashLoopBackOff**：容器反复崩溃重启的退避状态（是结果不是原因）
- **ImagePullBackOff**：镜像拉取失败的重试状态
- **describe 的 Events**：K8s 把每一步发生了什么写在这里 —— 排障第一入口

## 伸缩与监控（Lab 09 / 10）
- **HPA**：按指标自动增减副本数的控制器
- **metrics-server**：集群内指标聚合器，HPA 的数据源
- **RBAC**：基于角色的权限控制 —— ServiceAccount + Role + RoleBinding
- **hostNetwork**：Pod 直接共享节点网络栈（占节点端口，实验里用于访问宿主机服务）
- **ServiceAccount**：Pod 访问 K8s API 的身份；Spark driver 用它创建 executor
