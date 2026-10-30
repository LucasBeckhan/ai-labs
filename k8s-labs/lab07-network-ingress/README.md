# Lab 07 — 网络：Service、集群 DNS 与 Ingress

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> **新版必做入口：[手写、生产故障与验收](PRACTICE.md)**。先理解本页示例，再合上参考独立完成练习；只跑通示例不算过关。


## 📖 本章学习指导

> 建议时长 **2.5 小时** ｜ 前置：Lab 02/06 ｜ 关联面试：`interview-prep/01-kubernetes.md` Q10

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3
2. **跑**（60min）：web-broken 空 Endpoints 排障必做；**第 5 步 Ingress 的"端口冲突假阳性"是本 lab 灵魂**——三个 curl 对照（带 Host/无 Host/错 Host）必须全对才算真验证
3. **破坏练习**（20min）：① Service selector 改错一个字母，看 Endpoints 变空再修复；② 删 ingress-ready 节点标签，看 controller 卡 Pending
4. **验收自测**：① Service→Pod 数据平面？② 四种暴露方式选型？③ Ingress"看起来通但没走"怎么证明？
5. **产出**：一张"流量从浏览器到 Pod"的路径手绘图

## 学习目标

- 讲清 Service 找到 Pod 的原理（label → Endpoints），以及流量从集群外一路进到 Pod 的完整路径
- 熟练使用集群内 DNS 域名格式
- 理解 ClusterIP / NodePort / Ingress 三层入口的定位差异
- 会排"Service 没有后端"这种经典故障

## 核心问答

**Q1：Service 是怎么把流量导到 Pod 的？Pod 重启 IP 变了怎么办？**

> 参考答法：Service 通过 **label selector** 动态圈定后端 Pod，控制器实时维护 **Endpoints（endpoint slices）** 列表；每台节点上的 **kube-proxy** 把 Service 的规则写进 iptables/IPVS（nftables），访问 Service 虚拟 IP 时内核按规则 DNAT 到某个真实 Pod IP。Pod IP 确实会变，但 selector 跟着 label 走，Endpoints 自动更新 —— 客户端永远只认 Service 名字。

**Q2：集群内怎么访问一个 Service？DNS 域名是什么格式？**

> 参考答法：CoreDNS 提供集群 DNS。同 namespace 直接 `http://web`；跨 namespace 用 `web.<namespace>`；完整格式 `web.default.svc.cluster.local`。StatefulSet 的 Pod 还有单独域名：`<pod>.<headless-svc>.<ns>.svc.cluster.local`（Lab 04 里 nslookup 过 mysql-0）。

**Q3：Ingress 和 NodePort 的区别？什么时候用哪个？**

> 参考答法：NodePort 在**每个节点**开端口（30000-32767），四层转发，适合临时暴露、测试；LoadBalancer 是云厂商在 NodePort 外再分配一个外部负载均衡；**Ingress 是七层**，由 Ingress Controller（通常 Deployment 跑在集群里）按域名/路径把 HTTP 流量路由到不同 Service —— 一台入口 + TLS 终止 + 多业务复用，是生产标准姿势。链路总结：**用户 → LB → Ingress Controller Pod → 按 host/path 规则 → Service → Pod**。

## 动手实验

### 1. 部署三种 Service

```bash
cd lab07-network-ingress
kubectl apply -f manifests/web.yaml
kubectl get svc web web-nodeport web-broken
```

预期：

```
NAME           TYPE        CLUSTER-IP     PORT(S)
web            ClusterIP   10.96.x.x      80/TCP
web-nodeport   NodePort    10.96.x.x      80:30080/TCP
web-broken     ClusterIP   10.96.x.x      80/TCP     ← IP 照样有！故障藏在后端
```

### 2. 排障预演：web-broken 是个"空壳 Service"

```bash
kubectl get endpoints web web-broken
```

预期：`web` 有 3 个 Pod IP，`web-broken` 是 `<none>`。**Service 正常不代表链路通，Endpoints 为空 = selector 没圈到任何 Pod** —— 改 label 对上即可（这个 bug 在生产里以"配置手误"的形式反复出现）。

### 3. 从集群内部走一遍网络

```bash
# 用一个一次性 Pod 当"集群内用户"
kubectl run curl --rm -it --image=curlimages/curl --restart=Never -- sh
# 进入后依次执行：
curl -s web                     # 同 namespace 短域名
curl -s web.default.svc.cluster.local   # 完整域名
for i in 1 2 3; do curl -s web | grep title; done   # 多打几次，观察负载均衡（nginx 欢迎页无差别，看不出轮询，但 DNS/虚拟 IP 已验证）
nslookup web                    # 看 ClusterIP
exit
```

### 4. 从你的 Mac 访问 NodePort

```bash
curl -s http://localhost:8080 | head -3
```

预期：nginx 欢迎页 HTML —— 流量路径：`Mac:8080 → kind 节点容器 30080 → DNAT → Pod:80`。

### 5. 安装 Ingress Controller，按域名分流

> 清单已 vendor 到本地（`manifests/ingress-nginx-kind.yaml`，源自官方 controller-v1.11.3 的 kind 专用部署，已去掉镜像的 sha256 摘要锁定以便离线加载）；镜像已在准备阶段 `kind load` 进集群。

**第一步：给节点打标签。** kind 专用清单自带 `nodeSelector: ingress-ready=true`（Lab 06 的 nodeSelector 知识现学现用）—— 不打标签，controller Pod 会一直 Pending，报 `didn't match Pod's node affinity/selector`：

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE ingress-ready=true
kubectl apply -f manifests/ingress-nginx-kind.yaml
kubectl -n ingress-nginx rollout status deploy/ingress-nginx-controller --timeout=300s
```

**第二步：把 30080 让给 Ingress。** 这一步藏着一个必踩的坑：kind-config 把本机 8080 映射到节点的 30080，而上面第 4 步的 `web-nodeport` Service 正占着 30080 —— 如果直接安装，controller 的 Service 会被分配到随机端口，你 `curl localhost:8080` 打到的其实是 web-nodeport、**完全绕过了 Ingress**（两个都是 nginx 欢迎页，肉眼看不出区别 —— 笔者验证时就中了这个假阳性）。所以：删掉 web-nodeport 释放端口，再把 controller 的 Service 固定到 30080：

```bash
kubectl delete svc web-nodeport     # 释放 30080（ClusterIP 的 web 保留，Ingress 后端用它）
kubectl -n ingress-nginx patch svc ingress-nginx-controller \
  -p '{"spec":{"ports":[{"port":80,"nodePort":30080},{"port":443,"nodePort":32443}]}}'
kubectl apply -f manifests/ingress.yaml
```

**第三步：验证域名分流（三个对照）：**

```bash
printf "正确 Host:  "; curl -s -H "Host: demo.local" http://localhost:8080 | grep -m1 title
printf "无 Host:    "; curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080
printf "错误 Host:  "; curl -s -o /dev/null -w "%{http_code}\n" -H "Host: other.com" http://localhost:8080
```

预期：正确 Host 返回 nginx 欢迎页；无 Host 和错误 Host 都是 **404**（打到了 ingress-nginx 的默认后端）。三个结果对上，才说明流量真的经过了 Ingress 的 host 规则。

```bash
curl -s -H "Host: demo.local" http://localhost:8080 | head -3   # 带对 host → 通
curl -s http://localhost:8080 | head -3                          # 不带 → 404（Ingress 按 host 分流的直接证明）
```

### 6. Headless Service 直连 Pod（回收 Lab 04）

```bash
kubectl run dns-test --rm -it --image=busybox:1.36 --restart=Never -- sh -c \
  "nslookup web.default.svc.cluster.local && nslookup web-broken.default.svc.cluster.local"
```

预期：`web` 解析出 ClusterIP；`web-broken` 也解析出 ClusterIP（Service 的 IP 恒在），区别只在后端 Endpoints 是否为空 —— 再强化一遍"Service ≠ 后端可达"。

### 清理

```bash
kubectl delete -f manifests/
```

（留着不删也行，Lab 10 不依赖它；但为省内存建议删。）

## 观察与思考

1. iptables 模式和 IPVS 模式的区别，什么时候需要 IPVS？（iptables 规则线性匹配，Service/后端上万时延迟上升；IPVS 用哈希表 + 真实负载均衡算法。大规模集群选 IPVS —— 理解到"规模阈值"这一层就够了）
2. 你们公司的数仓/平台组件（Airflow UI、Spark History、Grafana...）在 K8s 里是怎么暴露给用户的？（十有八九就是 Ingress 按域名分流 —— 现在你能画出完整链路了）
3. 为什么"Service 创建成功"≠"服务可用"？（两层：Endpoints 是否为空；Pod readiness 是否通过 —— Endpoints 控制器只收 ready 的 Pod）

## 常见坑

- `kubectl run curl --rm -it` 进入交互 shell 后，Pod 名就是 curl，exit 即销毁
- Ingress 需要 Controller 才生效：只 apply Ingress 资源没有 Controller，地址栏永远是空的
- macOS 上 80/443 端口需 root，所以 kind-config 用 8080/8443 映射；curl 时**必须带 Host 头**（没有 DNS，host 规则靠 Header 匹配）
- ingress-nginx 镜像约 300MB，首次拉取慢属正常
