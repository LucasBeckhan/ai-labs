# 新业务沙箱验证记录

日期：2026-10-28（Asia/Shanghai）。环境：本机Docker Desktop、kind-labs，单节点Kubernetes v1.31.4，Python镜像python:3.12-alpine。全部为虚构训练数据，结果不代表公司业务已上线。

## 本次已执行

| 项目 | 实际结果 |
|---|---|
| 本地自动测试 | 12/12通过，覆盖统计、时区/窗口、重复归档/损坏归档、HTTP、配置更新、依赖故障、排空、路径和命名空间保护 |
| 教学Dockerfile | 构建成功；测试容器代码导入成功，UID=10001，容器已自动删除 |
| 部署与Service业务验收 | 2个Ready副本；EndpointSlice有后端；从Pod经Service访问两条demo-a线路和告警统计成功 |
| 业务数据 | raw_count=3、unique_count=2、E-001/E-002；不会将其他租户、窗口右边界或重复投递多算 |
| selector/port故障 | 注入后verify非零，恢复后集群内业务验证通过 |
| readiness/image故障 | 注入后发布完成门禁拒绝通过，恢复后业务验证通过；本次未等待完整镜像退避周期或覆盖所有仓库/网络失败 |
| pending故障 | 确认新Pod未绑定节点，PodScheduled条件/独立Events提示Insufficient cpu；恢复后通过 |
| 独立采集器crash | 观测到容器终止Error，程序设置exit 2；练习对象已清理 |
| 独立消费者OOM | 观测到terminated.reason=OOMKilled；练习对象已清理 |
| ConfigMap更新 | 不重启进程时文件label变green、环境快照仍blue；恢复后重新部署回到基线 |
| 依赖故障 | 所有API Pod退出Ready，重启计数保持0；恢复后业务验证通过 |
| 模拟安全周报 | Job完成且数字正确；首次created，再次同内容existing；没有外部发送 |
| 备份与恢复 | 从源PVC导出至Mac临时tar，再恢复至独立report-restore卷，报告文件sha256一致 |
| 最小RBAC | get configmap/demo-config=yes；get secrets=no；delete pods=no |
| 采证工具 | 可保存对象、独立Events、Pod原始JSON、EndpointSlice和API日志；不采集Secret |
| 文档与清单 | 新增Python/SVG语法、业务YAML语法与相对链接检查通过 |

源报告与恢复报告hash：`0bfecf704520ecad27cc1b6553191df8071945b39858f8e96442694db4c268cb`。统计输入与输出相同才适用该hash，不作为任意未来报表的固定值。

## 测试中发现并修正

- 本机describe输出不附带Events，采证另存get events，调度原因还读取PodScheduled条件；不靠固定sleep后找一段describe文本判断。
- ConfigMap投影有异步延迟，验证等实际文件变化，不假定固定一分钟。
- Docker镜像与ConfigMap投影的代码路径不同，修正默认fixture路径，另构建非root镜像验证导入。
- API仅有旧副本Ready不能当作发布成功，verify同时检查observedGeneration、updated/ready/available副本与Service实际请求。

## 尚未在本次执行

HPA负载与Metrics API、Ingress域名入口、Quota/Secret故障、SDK/真实云服务、Kafka消费、完整Job失败重试及CronJob并发、长连接退出、策略CNI、多节点drain/PDB/DaemonSet、跨节点/跨机房/云盘容灾。这些是任务册中的手写/独立环境题，不能由上述验证推导成功。

本程序无真实身份认证；固定tenant数据过滤不等于安全多租户。文件归档只能演示同内容重复运行，不提供分布式事务或崩溃一致性保证。ConfigMap挂代码是入门路径，生产应固化代码并记录镜像版本。

验证资源清理后，重新运行business/labctl.py up即可开始第一轮；临时测试命名空间和卷不作为长期保存位置。
