# Lab 01 — 容器基础：把一个 Java 应用打成"合格"的生产镜像

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **2 小时** ｜ 前置：会用终端执行命令即可 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q1-Q2

**学习循环（按序执行）：**
1. **读**（20min）：本页「学习目标 + 原理速讲 + 核心问答」，生词查 [GLOSSARY](../GLOSSARY.md)
2. **跑**（30min）：「动手实验」5 步逐条敲（第 4 步 JVM 限额实验是本章灵魂，必须亲眼看到 371MB）
3. **破坏练习**（20min）：① 删掉 Dockerfile 的 `USER app` 重建，观察 `user=` 变成 root 再恢复；② `--memory=512m` 改 64m 看输出变化
4. **验收自测**（10min）：不看文档回答——① 容器 vs 虚拟机一句话？② 多阶段构建省了什么？③ JVM 为什么要 MaxRAMPercentage=75？
5. **产出**：记录你镜像的总大小与基础镜像大小对比

**常见卡点**：拉不动镜像 → 跑 `hack/prepare-images.sh`；alpine 报 no matching manifest → 本文"常见坑"第 2 条

## 学习目标

- 理解容器与虚拟机的本质区别，能向任何人一句话讲清
- 会写**多阶段构建** Dockerfile，知道为什么最终镜像里不该有 JDK/Maven
- 理解镜像分层与缓存，会看 `docker history`
- 让 JVM 正确感知容器内存限额 —— 这是 Java 工程师上 K8s 之前**必补**的一课

## 核心问答

**Q1：容器和虚拟机的区别？**

> 参考答法：虚拟机通过 Hypervisor 虚拟出整套硬件，每个 VM 跑完整操作系统，隔离强但重；容器是**共享宿主机内核**的进程级隔离 —— 用 namespace 做视图隔离（PID/网络/文件系统等，让容器以为自己独占系统），用 cgroup 做资源限制（CPU/内存配额）。所以容器启动是秒级、开销是 MB 级，VM 是分钟级、GB 级。

**Q2：为什么生产镜像不要用完整 JDK？多阶段构建解决什么问题？**

> 参考答法：构建工具（JDK/Maven/源码）只在编译期需要，带着上线会增大镜像、拉长部署时间、扩大攻击面。多阶段构建用 `FROM ... AS build` 编译，第二个 `FROM` 只 `COPY --from=build` 编译产物，最终镜像里没有构建链路。

**Q3：Java 应用跑在容器里，堆内存该怎么设？**

> 参考答法：不要写死 `-Xmx2g` 这种和 K8s limits 脱节的值。JDK 8u191+/10+ 默认开启 `UseContainerSupport`，能感知 cgroup 限额，推荐用 `-XX:MaxRAMPercentage=75.0`（留 25% 给元空间、线程栈、直接内存）。如果 JVM 感知不到容器限额，堆会按宿主机内存算，pod 会莫名其妙 OOMKilled。

## 原理速讲

**镜像分层**：Dockerfile 每条指令产生一层，层可以被多个镜像共享、可缓存。所以把"不常变的"放前面（如下载依赖），"常变的"放后面（如 COPY 源码），构建才会快。`docker history` 能看到每一层。

**namespace + cgroup**：namespace 回答"能看到什么"（隔离视图），cgroup 回答"能用多少"（限制资源）。K8s 的 requests 用于调度，也会影响部分运行时权重；limits 通过 cgroup 等机制约束资源上限 —— 这个对应关系记住，Lab 05 会验证。

## 动手实验

### 1. 构建镜像

```bash
cd lab01-container-basics/app
docker build -t hello:v1 .
```

预期：先走 build 阶段（javac 编译），再走运行阶段。第二次构建会命中缓存秒完成。

### 2. 对比镜像体积，看看多阶段构建省了什么

```bash
docker images | grep -E "temurin|hello"
```

预期输出（体积可能略有差异）：

```
hello                      v1     ...   约 255MB
eclipse-temurin            17-jdk ...      476MB
```

最终镜像 ≈ JRE 基础层 + 一个 class 文件，比单阶段直接用 JDK 小一半左右。

### 3. 看清每一层是怎么来的

```bash
docker history hello:v1
```

你会看到 `addgroup`、`COPY Hello.class`、`ENTRYPOINT` 各占一层，底层是基础镜像的层。

### 4. 验证 JVM 感知容器内存限额（本实验核心）

```bash
# 限制 512MB 内存运行
docker run --rm --memory=512m hello:v1
```

**预期第一行输出：**

```
[Hello] JVM max heap = 371 MB      # ≈ 512MB × 75%（实际值有实现与对齐差异），说明正确感知了 cgroup 限额
[Hello] user = app                 # 非 root 用户
```

对照组：故意关掉容器感知，看堆变成多大 —— 这就是"没配对时的生产事故"：

```bash
docker run --rm --memory=512m --entrypoint java hello:v1 \
  -XX:-UseContainerSupport -XX:MaxRAMPercentage=75.0 -version 2>&1 | head -2
```

再跑一次不带 `-version` 的完整命令会看到 max heap 远大于 384MB（按宿主机内存算），这种 pod 一旦真的分配内存就会撞上 cgroup 限额被杀。

### 5. （进阶，30 秒）把镜像跑进 K8s，为后面所有实验铺路

```bash
cd ../..
# kind 的集群用的是自己的 containerd，不认识 Docker 里的镜像，需要导进去
kind load docker-image hello:v1 --name labs

kubectl run hello --image=hello:v1
kubectl logs hello | head -2
```

预期：logs 中能看到堆大小与用户。这里未设置 limits，不应期待固定 384 MB；对比 Docker 限额实验，并在后续手写 Pod 中补上内存 limits 验证。

清理：

```bash
kubectl delete pod hello
```

## 观察与思考

1. `--memory=512m` 这个 flag 写进 cgroup 的哪个字段？K8s 的 `resources.limits.memory` 又写到哪？（同一个字段 —— 这就是"K8s 资源限制 = cgroup 限制"的本质）
2. 如果 Dockerfile 里 `COPY Hello.java .` 放在 `RUN javac` 之前/之后，缓存行为有什么区别？（指令不变则缓存复用；把常变的源码放后面，依赖安装层才能命中缓存）
3. ENTRYPOINT 和 CMD 的区别？（ENTRYPOINT 是固定主命令，CMD 是默认参数、可被运行时覆盖；两者组合是最佳实践 —— 这也是 `--entrypoint java` 能生效的原因）

## 常见坑

- **不要**在 arm64 机器上给镜像强加 `--platform linux/amd64`（会走 QEMU 模拟，慢且行为怪异）；本文所有镜像都是双架构，直接构建即可
- **`eclipse-temurin:17-jre-alpine` 没有 arm64 版本**（Temurin 的 Alpine 变体只发布 x64），Apple Silicon 上拉取会报 `no matching manifest for linux/arm64/v8`，所以本实验用 `17-jre-jammy`；如果你需要在 Alpine 上跑 Java，选 `eclipse-temurin:17-jre-alpine` 的 x64 机器或改用 bellsoft/liberica-openjre-alpine（有 arm64）
- `kind load docker-image` 只对 kind 集群有效；集群重建后（`kind delete` + `create`）需要重新 load
