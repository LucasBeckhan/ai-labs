# 监控门户的Service、域名与入口

> 这是本章的云网安业务入口，全部使用虚构数据；不是公司真实部署规范。第一轮优先[6次快速实战](../business/FAST-TRACK.md)，本章再补齐对应原理。不要重复机械抄三份清单。

## 业务目标

客户页面不可达可能是selector、端口、DNS或Ingress任一层。

## 需要自己手写什么

手写Service selector/port/targetPort、Ingress host/path/class，标出80→8000流向。

从空白保存到本章work/；公共代码和fixture可以复用，配置必须解释字段及引用关系。先server dry-run再apply，名称避免覆盖其他章参考。namespace/SA等依赖要先存在，dry-run不会持久化前置对象。不能拿API接受当作功能正确。

## 具体实战

到[30题任务册](../business/DRILLS.md)完成 **01、02、25、26**。题号是统一编号；自动注入仅01–09，其他按题目手写/手动操作。正常基线与恢复命令见[业务沙箱](../business/README.md)。先对照一次参考，再独立重做，卡住15分钟后看折叠提示。

## 本章必须讲清的边界

port-forward不是完整入口验收，尤其不能替代集群内Service请求；Ingress需要Controller，别与旧NodePort抢端口。

## 过关标准

逐层验证Pod监听→Pod IP→Service/EndpointSlice→DNS→Ingress，至少修复selector/port两题。

交付手写YAML、故障前后证据、最小修复diff和一页复盘。复述“业务现象→机制→定位→恢复→预防”，不要只列kubectl命令。统一80分通过，无证据或业务验证重做；未具备指标/CNI/多节点环境的题单独标记未验证。
