# 6次实战掌握主线：每次60–90分钟

目标是先能部署、定位、恢复一个完整业务，再按14章补全原理与扩展。每次采用“10分钟理解→15分钟跑通→30分钟弄坏修好→15分钟从空白写/复述”。不用第一天就安装所有云平台和中间件。

## 第1次：交付网络监控API

前置Docker与labs；先完成[快速启动](README.md)。用浏览器查看线路与统计。画出ConfigMap→Pod→Deployment→Service关系，写出容器监听8000、Service暴露80的区别。

手写：不看参考，写自己的Deployment与Service到work/，名字增加练习后缀；保留探针、资源、labels对应关系，干跑后再apply。业务配置/代码CM可复用。用Service集群内请求验证，不仅看Running。

过关：解释为什么Docker本地有镜像还需kind load，为什么ConfigMap不在镜像里也能提供代码。对应Lab01/02/07。

## 第2次：客户说“监控页面访问不了”

按顺序做selector、port、dependency三题，每题先recover/verify建立基线，再fault。采证：Pod Ready、Service selector、EndpointSlice、探针日志、实际HTTP错误。

手写：自己的Service和探针配置。不要通过重建整个集群“解决”。dependency题等待CM同步，观察Ready下降与重启计数基本不变；不是仅readiness错误就删Pod。

过关：30分钟内区分选错后端、端口不符、依赖失败；每题两条证据和最小修复。对应Lab02/07/08。

## 第3次：版本发布与配置变更

依次做readiness、image、config。观察旧Pod仍接流量但发布没完成；用rollout与业务两种验收。配置题记录/config里的file_label和env_label，再重建Pod验证环境变量更新。

手写：滚动策略、readiness、环境变量与卷挂载。讲清ConfigMap可更新不等于所有程序自动重载，也不等于Deployment自动换Pod。

过关：给出业务止血（旧副本继续服务）和新版本最小修复，解释rollout undo不等于回滚所有配置。对应Lab03/11。

## 第4次：告警任务OOM与高峰扩容

做pending、crash、oom三题。pending的新旧副本资源分别查，crash看previous，oom看terminated.reason和分配日志。新建压力Pod有运行时限，结束清理。

可选：Metrics API可用后，运行HPA与120秒load，记录负载前中后副本/CPU/conditions。不可用先排metrics-server，不修改系统TLS设置凑结果。

手写：requests/limits、HPA CPU目标、扩缩容范围。过关：区分资源不足、程序报错、OOM与CPU限流；不能用加副本掩盖内存泄漏。对应Lab05/06/09。

## 第5次：安全周报、PVC与恢复

report运行两次，核对raw=3/unique=2与created/existing。进入DRILLS的卷与恢复题，把归档备份到Mac再恢复到新PVC；查询恢复内容和hash，不覆盖唯一原件。

手写：CronJob、失败重试、暂停与并发策略、卷挂载。过关：Job Complete不等于数字正确，PVC不等于备份，Forbid不等于业务幂等。对应Lab04/12/14。

## 第6次：权限、监控和盲测

应用专用RBAC对照；只读指定CM为yes、读Secret/删Pod为no。取/metrics并解释它只是业务请求计数，不是延迟P95/告警准确率。选择3个未看答案的故障，每题15分钟，最后做一次verify和证据复盘。

手写：最小Role/RoleBinding、一个指标抓取配置。过关：能说明身份、授权、网络隔离分别在哪层保证；单节点/无策略CNI的能力边界清楚。对应Lab10/11/13。

## 第二轮再补全

通过主线后，按每章BUSINESS-PRACTICE补做数据任务、Spark、Ingress、多节点维护、网络策略等任务。默认kind不执行NetworkPolicy；必须换支持策略的独立测试环境。三节点kind仍共用一台Mac，不能证明跨机房容灾。

结业交付：自己写的配置、至少9张故障记录、一个可恢复的报告归档、3分钟架构解释；不用提交一堆没有解释的截图。
