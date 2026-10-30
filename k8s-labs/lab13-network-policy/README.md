# DNS 与 NetworkPolicy 故障

> **云网安业务实战：[本章业务任务](BUSINESS-PRACTICE.md)**。先走6次快速路线，再补本章细节；旧PRACTICE保留作进阶考核。


> 使用新版训练路线；每次实验提交 YAML、故障证据、恢复验证和面试复述，按 [统一验收](../CURRICULUM.md) 评分。参考清单用于核对，必须先手写。

## 环境边界：先验前置，再实验

默认 kind 的网络插件不提供 NetworkPolicy 策略执行。本章 DNS 部分可在 labs 练习；策略隔离部分必须使用已安装支持 NetworkPolicy 的 CNI 的独立测试集群（如按所选版本的 Cilium/Calico 官方安装流程配置）。不要在现有 labs 上随意替换 CNI。仅 API 接受 NetworkPolicy 不代表策略生效。

## DNS 实战（45 分钟）

在专用 namespace k8s-practice-13 中手写 nginx Deployment 与 ClusterIP Service `web`，启动 busybox:1.36 的 sleep 调试 Pod `client`。复用 Lab07 的结构，但不能直接复制整份文件。

```bash
kubectl --context kind-labs -n k8s-practice-13 exec client -- nslookup web
kubectl --context kind-labs -n k8s-practice-13 exec client -- nslookup web.k8s-practice-13.svc.cluster.local
kubectl --context kind-labs -n k8s-practice-13 exec client -- wget -T 3 -qO- http://web
kubectl --context kind-labs -n k8s-practice-13 get endpointslices -l kubernetes.io/service-name=web
```

失败则先检查 client/web Ready、Service selector 和实际集群 DNS 域，再排 DNS。故障 A：请求拼错 Service 名。B：在另一 namespace 使用短名 web，再改用正确全名。保存 NXDOMAIN/解析结果与 HTTP 请求结果，区别“解析失败”和“能解析但连接失败”。

## 策略任务（支持策略的独立集群，60 分钟）

先记录新集群 context，以每条命令显式 `--context <测试context>` 执行；不要沿用 kind-labs。创建同名专用 namespace 与 web/client 对象。

手写四份策略：① 全 namespace 默认拒绝 ingress/egress；② 允许 client 到 web 的 TCP/80；③ 允许 web 接收 client 的 TCP/80；④ 允许 client 到集群 DNS 的 UDP/TCP 53（按实际 CoreDNS namespace、Pod labels、服务解析路径配置，不能盲抄标签）。

依次记录：无策略时 HTTP 成功；默认拒绝后 Pod IP 直连超时；仅允许业务但未放 DNS 时 DNS 失败；补全 DNS 后 Service 请求恢复；未授权 client 仍失败。NetworkPolicy 是多份允许规则的并集，并且连接两端的 ingress/egress 都要允许；策略不规定精确 HTTP 错误码。

## 验收与清理

产出四格访问矩阵（授权/未授权 × DNS/HTTP），附真实请求与策略 YAML。未具备 CNI 时明确标注“仅完成 DNS，策略未验证”，不能宣称隔离成功。

面试：Service selector 错误、CoreDNS 故障、NetworkPolicy 拒绝如何逐层区分？为什么连 IP 成功但域名失败？策略与 RBAC 各管什么？

在各自 context 删除本章专用 namespace；保留共享 CNI 和系统 DNS。

参考：[NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)、[DNS 排障](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)。
