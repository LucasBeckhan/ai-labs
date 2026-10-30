# Lab 04 — StatefulSet + PV/PVC：在 K8s 上跑一个"记性好的" MySQL

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **2 小时** ｜ 前置：Lab 01 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q8

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3，背下"PVC 提需求、SC 定标准、PV 是交付物"
2. **跑**（50min）：MySQL 启动慢（首初始化约 1 分钟）属正常；**第 4 步"数据到底在哪"必须做**——去神秘化是本实验的灵魂
3. **破坏练习**（20min）：① 删 PVC 再删 Pod，亲眼看数据消失（理解 Retain/Delete）；② replicas 改 2，看 mysql-1 与第二个 PVC 自动创建
4. **验收自测**：① 三者绑定链路？② StatefulSet 两大承诺？③ Headless Service 解决什么？④ RWO 对"多副本共享存储"意味着什么？
5. **产出**：`kubectl get pvc,pv,sc` 三条资源齐全的截图

## 学习目标

- 搞懂 PV / PVC / StorageClass 三者的关系和绑定链路（本实验最核心的一条链路）
- 理解 StatefulSet 两大承诺：**稳定的网络身份** + **稳定的存储**
- 亲手验证：Pod 被删掉重建后，数据还在 —— 以及弄明白数据到底存在哪
- 顺带掌握 Secret 的标准用法

## 核心问答

**Q1：StatefulSet 和 Deployment 的区别？**

> 参考答法：Pod 有无"身份"的区别。Deployment 的 Pod 是**可替换的匿名副本**（名字随机、共享 PVC 或无盘）；StatefulSet 的 Pod 有**稳定序号身份**（mysql-0、mysql-1...，重建后同名同盘）+ 按序部署/删除（0 起好才起 1），配 Headless Service 后每个 Pod 有独立 DNS（`mysql-0.mysql.ns.svc.cluster.local`）。适用：数据库、Kafka、ZK、ES 这类"身份和本地状态有意义"的组件。

**Q2：PV、PVC、StorageClass 的关系？**

> 参考答法：PVC 是用户的"存储申请单"（要多大、什么模式）；PV 是实际的存储资源；StorageClass 是"存储模板/供应商"，负责**动态供应** —— 没有现成 PV 时，SC 自动创建 PV 来满足 PVC。绑定链路：StatefulSet 的 volumeClaimTemplates → 为每个 Pod 创建 PVC → SC 的 provisioner（kind 里是 local-path-provisioner）创建 PV 并在节点上真的建目录 → Pod 挂载。三者的关系一句话：**PVC 提需求，SC 定标准，PV 是交付物**。

**Q3：Headless Service 是什么，为什么 StatefulSet 需要它？**

> 参考答法：`clusterIP: None` 的 Service，不做虚拟 IP 和负载均衡，DNS 直接解析到**每个 Pod 自己的 IP**。普通 Service 的 DNS 只解析到 Service IP，Pod 重启 IP 变化，客户端无感知但也没法"点名"某个 Pod；主从复制、分片集群必须能点名 mysql-0、mysql-1，所以需要 Headless。

## 原理速讲

kind 集群自带 StorageClass `standard`（rancher local-path-provisioner 实现），在节点容器里建真实目录，`kubectl get sc` 可见。实验里 PVC → PV → 宿主机目录的映射最后会亲眼看到。

**RWX/RWO**：`ReadWriteOnce` 单节点读写（数据库标配）；`ReadWriteMany` 多节点（NFS 类）。local-path 只支持 RWO —— 所以"把同一个盘挂给多个 Spark executor"这种需求在 K8s 里要靠对象存储/HDFS，而不是共享盘，这是数仓同学最容易踩的认知差。

## 动手实验

### 1. 部署并观察绑定链路

```bash
cd lab04-statefulset-storage
kubectl apply -f manifests/mysql.yaml

kubectl get pods -w     # 等 mysql-0 变 1/1（首次初始化约 1 分钟）
kubectl get pvc,pv,sc
```

预期：

```
NAME                                 STATUS   VOLUME                                     CAPACITY
persistentvolumeclaim/data-mysql-0   Bound    pvc-xxxxx                                  2Gi
NAME                                                        STORAGECLASS
persistentvolume/pvc-xxxxx   2Gi   RWO   Delete   standard
NAME                    PROVISIONER             RECLAIMPOLICY
storageclass.standard   rancher.io/local-path   Delete
```

三条资源一个不少 —— 这就是 Q2 里说的完整链路。注意 `volumeClaimTemplates` 自动生成了名为 `data-mysql-0` 的 PVC（模板名-数据Pod名）。

### 2. 写入数据

```bash
kubectl exec -it mysql-0 -- mysql -uroot -plab4pass -e "
CREATE DATABASE lab4;
USE lab4;
CREATE TABLE t (id INT, ts DATETIME DEFAULT NOW());
INSERT INTO t (id) VALUES (1),(2),(3);
SELECT * FROM t;"
```

预期：3 行数据。

### 3. 杀掉 Pod，验证"记性"

```bash
kubectl delete pod mysql-0
kubectl get pod -w    # 等它重新 Running（StatefulSet 控制器重建同名 Pod）
```

关键点：新 Pod **还叫 mysql-0**（Deployment 会叫 mysql-xxxxx 新名字），并且重新绑回同一个 PVC。

```bash
kubectl exec -it mysql-0 -- mysql -uroot -plab4pass -e "SELECT * FROM lab4.t;"
```

预期：3 行数据还在。

### 4. 追根问底：数据到底在哪？

```bash
kubectl get pv -o jsonpath='{.items[0].spec.local.path}'; echo
# 到节点（kind 的容器）里看
docker exec labs-control-plane ls -la $(kubectl get pv -o jsonpath='{.items[0].spec.local.path}')
```

预期：能看到 mysql 的 ibdata、lab4 目录 —— **所谓持久化，就是 PVC 把宿主机上一个真实目录映射进了容器**。这个"去神秘化"的视角对排障极有用。

### 5. 观察 StatefulSet 的 DNS（为 Lab 07 预热）

```bash
kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -- \
  nslookup mysql-0.mysql.default.svc.cluster.local
```

预期：解析出 mysql-0 的 Pod IP —— 每个 Pod 有了"身份证"。

### 清理

```bash
kubectl delete -f manifests/    # PVC/PV 会随 namespace 资源一起删除（注意：数据没了）
```

## 观察与思考

1. 把 StatefulSet 的 `replicas` 改成 2 会发生什么？（自动建 mysql-1 和第二个 PVC —— 单机 MySQL 主从的第一步；真实场景还要配复制账号，属于数据库同学的地盘，但架构你现在已经懂了）
2. PV 的 `reclaimPolicy: Delete` 是什么意思？删了 PVC 会怎样？（PV 连带删除，local-path 会清目录；生产数据库一般设 `Retain` 防误删）
3. 为什么 Kafka on K8s 也用 StatefulSet？（broker id 稳定 + 每副本独立盘，和 mysql-0 的逻辑完全一致 —— 学的是模式，不是某个产品）

## 常见坑

- mysql:8.0 首次启动初始化较慢，readinessProbe 的 `initialDelaySeconds` 别设太短，否则反复重启
- 实验 Secret 里是弱密码，生产用 `kubectl create secret` + 外部密钥管理（Vault/云 KMS）
- `delete -f` 后 PVC 不一定立刻消失（finalizer），确认 `kubectl get pvc` 为空再做下一个实验
- local-path 的 PV 路径在 kind 节点容器内，`docker exec labs-control-plane` 才能看到 —— 注意不是你的 Mac 本机路径
