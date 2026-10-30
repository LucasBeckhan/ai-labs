# Lab 08 — 排障实战：五种经典故障的"急救室"

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **2 小时** ｜ 前置：Lab 02/05/06 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q11-Q12 ｜ **值班能力周**

**学法变化**：先只看 `get pod` 的 STATUS **猜**病因，再 describe 验证——五病人全猜对才算过。
1. **跑**（30min）：一键放倒 5 个病人，逐个走"现象→describe→根因"
2. **破坏练习**（30min）：把 5 个病人的修复方法各写一行，然后**自己制造同类故障**（改错 tag/写错 selector）再修
3. **验收自测**：五种状态的第一排查命令各是什么？CrashLoopBackOff 是原因还是结果？137/1/143 三种退出码各自含义？
4. **产出**：自己的"排障卡片"（症状→第一眼→真相在哪→修复），这是你值班时的随身手册

## 学习目标

一次遇到 5 个生产高频故障，练成固定肌肉记忆。**排障能力是"能不能独立值班"的分水岭。**

## 核心问答

**Q：遇到 Pod 异常，你的排查顺序是什么？**

> 参考答法（背成条件反射）：
> 1. `kubectl get pod` 看 **STATUS**（先分类：Pod 级异常还是应用级异常）
> 2. `kubectl describe pod` 看 **Events**（调度失败/镜像拉取失败/探针失败，90% 的答案在这）
> 3. `kubectl logs [--previous]` 看应用日志（容器起来了才看得到；`--previous` 是上一次崩溃现场）
> 4. `kubectl exec` 进容器验证（进程、端口、配置文件）
> 5. 还不行就看上游：Node（`kubectl describe node` 内存/磁盘压力）、Service/Endpoints、Ingress
>
> 一句话总结：**先看状态分类，再读事件定位，日志和 exec 验证，最后才怀疑平台**。

## 动手实验

### 0. 一键放倒 5 个病人

```bash
cd lab08-troubleshooting
kubectl apply -f manifests/faults.yaml
kubectl get pod -l patient
```

预期（约 1 分钟后，p2/p5 的 RESTARTS 会开始涨；**注意这些 STATUS 会随重启退避在 Running/Waiting/Error 之间波动**，某个瞬间不一定和下面完全一致）：

```
NAME                READY   STATUS                       RESTARTS
p1-bad-tag          0/1     ImagePullBackOff             0        （前一分钟可能显示 ContainerCreating/ErrImagePull）
p2-crashloop        0/1     CrashLoopBackOff 或 Error    1+
p3-too-big          0/1     Pending                      0
p4-missing-config   0/1     CreateContainerConfigError   0
p5-bad-probe        1/0     Running                      1+
```

### 病人 1 — ImagePullBackOff：镜像名/tag 错误

```bash
kubectl describe pod p1-bad-tag | grep -A 4 "Failed to pull"
```

预期（两行都可能出现，看 pull 的具体报错）：

```
Failed to pull image "nginx:1.27-typo-not-exist": ... manifest unknown / not found   ← 网络正常时
Failed to pull image "nginx:1.27-typo-not-exist": ... dial tcp ...: i/o timeout      ← 访问不到仓库时
```

> 刚创建的前 1~2 分钟 STATUS 可能是 `ContainerCreating`（第一次拉取还在超时重试中），要等事件出现。思维定式：ImagePullBackOff 有三种根因——**名字/tag 错**（本例）、**私有仓库没认证**（配 imagePullSecrets）、**网络/限流**（公共仓库 rate limit 或本机网络不通）。describe 里的报错原文能直接区分这三种。生产里还有第四种：多节点集群里部分节点没拉到（某节点网络问题）——用 `kubectl get events -A | grep Pull` 聚合看。

### 病人 2 — CrashLoopBackOff：启动即崩

```bash
kubectl logs p2-crashloop --previous | tail -3
```

预期：`starting...` 后无下文 —— 看到进程"echo 完 2 秒就退出"，根因即明。**CrashLoopBackOff 是"容器反复崩溃"的结果状态，不是原因**；日志里的最后几行才是死因（应用级错误、依赖连不上、配置错）。

> 两个现实细节：① 随着退避间隔变长（10s→20s→40s→…→5min），STATUS 会在 `Running`（正在跑第 2 秒）、`CrashLoopBackOff`（等待重启）、`Error`（刚退出）之间波动；② `--previous` 偶尔返回 `unable to retrieve container logs`（containerd 已轮转旧容器日志），重试或改看当前日志即可。

> 对照病人 5：同样是"反复重启"，一个是"主动崩溃"，一个是"被探针杀掉"—— 症状相似，病因相反，`describe` 里的 `Liveness probe failed: HTTP probe failed with statuscode: 404` 事件是分水岭。

### 病人 3 — Pending：调度不进去

```bash
kubectl describe pod p3-too-big | grep -A 2 FailedScheduling
```

预期：`0/1 nodes are available: 1 Insufficient cpu, 1 Insufficient memory.`（本例 CPU 要 200 核、内存要 300Gi，双双超出；括号里的具体数字以集群为准）。requests 写得太贪心是生产 Pending 第一大原因；结合 Lab 06 的污点/亲和原因，Pending 病历本就齐了。

### 病人 4 — CreateContainerConfigError：配置引用悬空

```bash
kubectl describe pod p4-missing-config | tail -5
```

预期：`CreateContainerConfigError ... configmap "i-do-not-exist" not found`。

> 注意它和 `ContainerCreating` 的区别：容器**还没创建就卡住**了，`logs` 一定是空的 —— 这是"别急着看日志，先看事件"的最佳例证。

### 病人 5 — 探针配错：应用活着却被反复重启

```bash
kubectl describe pod p5-bad-probe | grep -B 1 -A 3 "Liveness"
kubectl logs p5-bad-probe | tail -2        # 日志里连 nginx 启动横幅都反复出现
```

> 这是最阴险的故障：STATUS 显示 Running、READY 1/0 交替，监控里"服务时好时坏"。修复：探针路径改成 `/`（或删掉探针）。**给运维同事的教训：探针是双刃剑，上线前务必先用 readiness 验证路径正确。**

### 收尾

```bash
kubectl delete -f manifests/faults.yaml
```

## 观察与思考（把 5 个病例串成知识网）

| 症状 | 第一眼看 | 真相在哪 | 对应原理实验 |
|---|---|---|---|
| ImagePullBackOff | STATUS | describe 的 pull 报错 | Lab 01 |
| CrashLoopBackOff | STATUS | logs --previous | Lab 02（探针/退出） |
| Pending | STATUS | describe 的 FailedScheduling | Lab 05/06 |
| CreateContainerConfigError | STATUS | describe 的事件 | Lab 02（挂载） |
| 反复重启但 Running | RESTARTS | describe 的 probe 事件 | Lab 02/03 |

1. `kubectl get events --sort-by='.lastTimestamp' -A` 值得设成 alias —— 按时间线看全集群事件，多 Pod 连环故障时是第一入口
2. `kubectl logs` 空但 STATUS 非 Pending 时，先想"容器到底创建出来没有"（ConfigError/ContainerCreating），再想"是不是被 OOM 杀了"（describe 看 Last State）

## 常见坑

- 本实验文件**故意**全是错的，不要"顺手修复"后重新 apply —— 那 5 个病例就没得看了
- p5 的探针失败重启有退避间隔（10s/20s/40s...最长 5 分钟），RESTARTS 涨得慢是正常的，不用等
- 排障时 `--all-namespaces`（`-A`）是老手习惯：故障经常不在你以为的 namespace 里
