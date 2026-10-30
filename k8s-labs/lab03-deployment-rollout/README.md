# Lab 03 — Deployment 滚动更新与回滚：模拟一次线上发布

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **1.5 小时** ｜ 前置：Lab 02 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q4

**学习循环：**
1. **读**（15min）：核心问答 Q1-Q3
2. **跑**（40min）：发布 v2 时盯住 `get rs -w`（RS 数量变化是本实验的眼）；金丝雀 pause 必做；坏镜像被刹车必做
3. **破坏练习**（20min）：① 删掉 readinessProbe 再滚动更新，亲眼看"坏版本瞬间替换好版本"的灾难；② maxUnavailable 改 2 观察容量下降；都恢复
4. **验收自测**：① 三层关系与滚动更新原理？② maxSurge/maxUnavailable 语义？③ 回滚的本质？④ readiness 是什么"刹车"？
5. **产出**：一条 `kubectl rollout undo` 后 RS 的状态记录

## 学习目标

- 看懂 Deployment / ReplicaSet / Pod 三层结构，以及滚动更新时三者各自发生什么
- 掌握 `maxSurge` / `maxUnavailable` 的容量语义，能根据业务设计发布节奏
- 会用 `rollout pause/resume` 做简化版金丝雀发布
- 会回滚，并知道回滚"回"的是什么

## 核心问答

**Q1：Deployment、ReplicaSet、Pod 是什么关系？滚动更新时发生了什么？**

> 参考答法：Deployment 管理 ReplicaSet（每次改 Pod 模板都会**新建一个 RS**，旧 RS 保留），RS 管理 Pod 副本数。滚动更新时 Deployment 按节奏调两个 RS 的副本数：新 RS 从 0 涨到 replicas，旧 RS 从 replicas 降到 0，速率由 `maxSurge`（最多同时多出多少 Pod）和 `maxUnavailable`（最多同时缺多少 Pod）控制。新版就绪（readiness 通过才算数）才继续放旧的，这就是"滚动"的含义。

**Q2：maxSurge=1, maxUnavailable=0 意味着什么？**

> 参考答法：更新全程**可用容量永不缩水** —— 每次先多起 1 个新 Pod（4→5），等它 readiness 通过，再杀 1 个旧 Pod（5→4）。适合流量敏感服务；代价是更新期间需要能容纳临时多出的资源。反过来 maxSurge=0, maxUnavailable=1 是"先减后加"，省资源但容量下降，适合后台任务。

**Q3：回滚是怎么实现的？**

> 参考答法：`rollout undo` 不是"撤销操作"，而是**把上一个 ReplicaSet 的 Pod 模板重新设为期望状态** —— 本质还是一次滚动更新（反向的）。所以回滚同样受 maxSurge/maxUnavailable 控制、同样要等 readiness。`revisionHistoryLimit` 之外的旧 RS 会被清理。

## 动手实验

### 1. 部署 v1 并观察三层结构

```bash
cd lab03-deployment-rollout
kubectl apply -f manifests/deployment.yaml

kubectl get deploy,rs,pod -l app=web
```

预期（注意 RS 名字里那段随机 hash `pod-template-hash`）：

```
NAME              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.web    4/4     4            4           20s
NAME                   DESIRED   CURRENT   READY   AGE
replicaset.web-7d9f8c  4         4         4       20s
NAME                        READY   STATUS    AGE
pod.web-7d9f8c-xxxxx        1/1     Running   20s
```

关键理解：**只有当前 RS 是 4 副本，旧 RS 永远缩到 0 但保留**。`pod-template-hash` 是新旧 Pod 不会混淆的保证。

### 2. 发布 v2：观察滚动节奏

```bash
# 终端 1 盯事件
kubectl get rs,pod -w

# 终端 2 发布
kubectl set env deployment/web RELEASE=v2
kubectl rollout status deployment/web
```

预期：`waiting for deployment "web" rollout to finish...`，-w 终端里新 RS 副本 0→1→2→3→4，旧 RS 4→3→2→1→0，全程 READY 始终 ≥ 4（maxUnavailable=0 的效果）。

```bash
kubectl get pods -l app=web -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].env[0].value}{"\n"}{end}'
```

预期：4 个 Pod 全部 `v2`。

### 3. 金丝雀：pause 一下，让新版本只上一个

```bash
kubectl rollout pause deployment/web
kubectl set env deployment/web RELEASE=v3
kubectl get rs -l app=web --sort-by=.metadata.creationTimestamp
```

预期：三个 RS 并存，最新的（v3）`DESIRED=1`（pause 会先滚 1 个出来就停），v2 的旧 RS 仍是 4。

```bash
# 相当于 20% 流量在新版本上 —— 观察没问题再放行
kubectl rollout resume deployment/web
kubectl rollout status deployment/web
```

> 这就是金丝雀的原理骨架：生产上的金丝雀还要配合 Ingress 按权重分流（Lab 07）和监控指标（Lab 10），但"pause 控制新旧版本比例"这个内核是一样的。

### 4. 回滚

```bash
kubectl rollout history deployment/web        # 看有哪些版本
kubectl rollout undo deployment/web           # 回到上一个版本
kubectl rollout status deployment/web
kubectl get pods -l app=web -o jsonpath='{range .items[*]}{.spec.containers[0].env[0].value}{"\n"}{end}' | sort | uniq -c
```

预期：`4 v2`（若多出一行 `1 v3` 是刚被替换、正在优雅终止的残留 Pod，几秒后消失）。你会看到一条 Warning 提示 `last-applied-configuration` 注解未更新 —— 这是 `set/undo` 这类"改活动对象"和 `apply`（声明式）混用的经典提醒，工程实践里以 Git 里的 YAML 为准。再试 `--to-revision=<N>` 回滚到指定版本。

### 5. 看一次"失败发布"被自动刹住

```bash
kubectl set image deployment/web nginx=nginx:1.27-typo   # 不存在的 tag
kubectl rollout status deployment/web --timeout=15s || true
kubectl get rs -l app=web
```

预期：新 RS 卡在 `DESIRED=1, CURRENT=1, READY=0`，旧 RS 保持 4 —— **坏版本不会替换掉好版本**（kubectl 里旧 RS 没缩，maxUnavailable=0 也兜住了）。用 Lab 08 的方法 `kubectl describe pod` 能看到 ImagePullBackOff。

清理现场（把镜像改回来）：

```bash
kubectl rollout undo deployment/web
kubectl delete -f manifests/
```

## 观察与思考

1. 为什么改了 Pod 模板必然产生新 RS，而不是原地更新容器？（Pod 不可变性 —— 运行中的 Pod 除 image 等极少数字段外不可改，这是 K8s 一致性的基石，也是"Pod 随时可以被杀掉重建"的前提）
2. `kubectl rollout undo` 和"再 set 一次旧版本"在 RS 层面的区别？（前者复活旧 RS，revision 链不变；后者又建一个新 RS —— history 会多一条）
3. readinessProbe 在滚动更新里扮演什么角色？（**它是滚动更新的刹车**：没有它，Pod 起来就算就绪，坏版本会瞬间替换掉全部好版本）

## 常见坑

- `kubectl set env` / `set image` 改的是 Deployment 的模板 —— 对应生产里改 Git 里的 YAML（手改集群再改 Git 会导致漂移，工程实践应以 Git 为准：GitOps 思想，Lab 10 结尾有延伸）
- 滚动更新卡住十有八九是 readiness 过不了或资源不够，用 `kubectl describe` 看事件，别干等
- revisionHistoryLimit 设太小会没有版本可回滚
