# 监控平台发布与止血

> 这是本章的云网安业务入口，全部使用虚构数据；不是公司真实部署规范。第一轮优先[6次快速实战](../business/FAST-TRACK.md)，本章再补齐对应原理。不要重复机械抄三份清单。

## 业务目标

发布新版本时客户仍能查询线路，坏版本不能覆盖健康旧副本。

## 需要自己手写什么

手写两副本、selector/template labels、maxSurge/maxUnavailable、progressDeadlineSeconds与readiness。

从空白保存到本章work/；公共代码和fixture可以复用，配置必须解释字段及引用关系。先server dry-run再apply，名称避免覆盖其他章参考。namespace/SA等依赖要先存在，dry-run不会持久化前置对象。不能拿API接受当作功能正确。

## 具体实战

到[30题任务册](../business/DRILLS.md)完成 **03、04、10、11**。题号是统一编号；自动注入仅01–09，其他按题目手写/手动操作。正常基线与恢复命令见[业务沙箱](../business/README.md)。先对照一次参考，再独立重做，卡住15分钟后看折叠提示。

## 本章必须讲清的边界

能访问旧版本不代表新版本发布成功；回滚Deployment模板不会回滚可变CM，也不能回滚数据库变更。

## 过关标准

旧RS继续Ready，新RS失败有根因，修复后updated/ready与实际release一致，保存一次undo证据。

交付手写YAML、故障前后证据、最小修复diff和一页复盘。复述“业务现象→机制→定位→恢复→预防”，不要只列kubectl命令。统一80分通过，无证据或业务验证重做；未具备指标/CNI/多节点环境的题单独标记未验证。
