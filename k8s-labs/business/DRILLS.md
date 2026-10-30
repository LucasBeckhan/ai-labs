# 30个云网安实战任务

所有场景均为模拟；从k8s-labs目录执行。每题先 `python3 business/labctl.py recover`、`verify`，注入单个故障，再保存两条证据、手动修复、验证业务。不要连续叠加故障。1–9可自动注入，10–30提供手写/手动任务；不能把未做的任务算成已掌握。

## 第一组：9个可注入故障（每题15–25分钟）

通用命令：`python3 business/labctl.py fault <名称>`。采证：`python3 business/labctl.py capture --output business/work/<题号>`。capture保存对象、独立Events、Pod描述和原始JSON、EndpointSlice及API日志，不包含Secret。本机describe可能不附带Events，务必另外运行 `kubectl --context kind-labs -n cec-k8s-practice get events --sort-by=.metadata.creationTimestamp`，并检查PodScheduled条件中的message。

| 题号/名称 | 业务情境 | 必须拿到的两条证据 | 手动修复的对象与验收 |
|---|---|---|---|
| 01 selector | 监控页面突然不可访问 | Pod Ready；Service无匹配EndpointSlice | 修Service selector，verify通过 |
| 02 port | 服务后端存在但无法访问 | EndpointSlice有地址；实际监听8000与targetPort不同 | 修targetPort，集群内请求通过 |
| 03 readiness | 网络平台新版本发布停滞 | 新Pod探针404；旧RS仍Ready | 修新模板探针；rollout完成再verify |
| 04 image | 发布后新副本无法启动 | 镜像tag；Events中拉取失败原因 | 修镜像；区分错误tag、鉴权、网络，不只删Pod |
| 05 pending | 云资源不足导致新副本挂起 | Pod未绑定节点；FailedScheduling/Insufficient cpu | 修requests/limits；不改节点容量伪造结果 |
| 06 config | 配置下发后不同读取方式结果不同 | /config里file_label=green、env_label=blue | 等挂载同步；重建后env变green，再恢复blue |
| 07 dependency | 下游依赖故障，监控API退出服务池 | Ready=False；liveness正常且重启计数不增 | 恢复配置中的依赖标志，等Ready后verify |
| 08 crash | 独立告警采集器启动失败 | exitCode=2；当前/previous日志缺配置 | 复制Pod到work修command后重建；原故障Pod有90秒上限 |
| 09 oom | 独立告警消费者内存失控 | terminated.reason=OOMKilled；分配量与limit | 先改为有界消费/分批释放，不只提高内存；原故障Pod最多60秒 |

1–7观察的核心对象是monitor-api；8/9是独立的collector-crash、consumer-oom。不要因主API verify通过就说独立采集器正常。8/9须额外检查对应Pod和日志；`logs --previous`只在已有上一轮容器时适用。

<details>
<summary>卡住后再看：最小修复提示</summary>

- 01：selector.app应匹配monitor-api的Pod labels。
- 02：Service.port=80，targetPort=http；容器http端口8000。
- 03：readiness使用/readyz；liveness使用/healthz；startup使用/startupz。
- 04：正常镜像python:3.12-alpine；不要误以为Docker本地存在就等于每个kind节点都有。
- 05：请求100m/64Mi，limit500m/128Mi；requests必须不大于limit。200 CPU用于模拟调度失败，不是200m。
- 06：代码每个请求重新读/config/settings.json，所以文件可以热更新；ENV_LABEL是启动时快照。更新CM不自动触发Deployment换Pod。
- 07：dependency_ok恢复true；这里是教学开关，不是真实依赖探测。
- 08：Pod很多字段不可原地改，保存修复YAML再删除/重建自己的练习Pod；查exitCode和应用日志，别盲目配探针。
- 09：OOMKilled是比exit137更有力的证据；生产还需区分泄漏、峰值和容量，使用有限批次验证内存边界。

最后可用recover核对基线，但它不是你自己的最小修复。必须先保存故障证据和自己的配置diff。

</details>

## 第二组：发布、生命周期与观测

### 10. 发布版本与回滚（25分钟）

```bash
kubectl --context kind-labs -n cec-k8s-practice set env deployment/monitor-api RELEASE=v2
kubectl --context kind-labs -n cec-k8s-practice rollout status deployment/monitor-api --timeout=60s
kubectl --context kind-labs -n cec-k8s-practice rollout history deployment/monitor-api
kubectl --context kind-labs -n cec-k8s-practice rollout undo deployment/monitor-api
```

自己验证两个新副本的release先v2后v1，不能只请求一次Service就认为全量更新。交付：模板diff、RS关系、业务结果。追问：镜像tag没变、代码CM变了，undo能回滚代码吗？

### 11. 写错selector的API拒绝（15分钟）

从空白写Deployment，故意让selector与template labels不匹配，用server dry-run保存拒绝。与第05题对照：一个API拒绝，一个创建后调度失败；不能都叫Pending。提交修复后独立名称的Deployment/Service，避免覆盖参考。

### 12. 慢启动保护（20分钟）

将WARMUP_SECONDS设为20，记录startupProbe未通过时的状态、重启计数及首次Ready时间。再在work副本中给startupProbe过小failureThreshold复现启动被杀，修回足够窗口。CPU压力和调度时间也影响观测，不能精确等于某个秒数。

### 13. 优雅停止（20分钟）

新开终端持续follow一个Pod的日志，另一个终端删除该Pod；观察sigterm、shutdown_complete和Deployment补副本。进阶：加入10秒模拟清理、宽限期先20后2，比较清理日志；原程序只有短请求，不代表已验证长连接/在途事务零损失。不要通过preStop固定sleep宣称万能零停机。

### 14. 资源单位与安全上下文（20分钟）

手写两个独立Pod，分别设置100m与1 CPU请求，对比describe里的配置；解释Mi/Gi、m的单位。执行API Pod内`id`，验证UID10001、只读根文件系统，尝试写/tmp应失败；新增emptyDir挂载到明确写路径后再验证。不要为了写临时文件直接恢复root。

### 15. 高峰期HPA（30分钟，可选指标前置）

先确认 `kubectl --context kind-labs top pods -n cec-k8s-practice` 可用，检查原Lab09的Metrics API；没有指标就记录依赖缺失。

```bash
kubectl --context kind-labs -n cec-k8s-practice apply -f business/manifests/hpa.yaml
kubectl --context kind-labs -n cec-k8s-practice apply -f business/manifests/load.yaml
kubectl --context kind-labs -n cec-k8s-practice get hpa -w
```

load最多120秒，记录负载前中后的CPU、HPA conditions、副本数。要求实际看到指标与扩缩容过程，否则标未验证。recover移除HPA与负载并恢复2副本；不要apply固定replicas与HPA同时争抢。此负载是有界CPU模拟，不是Kafka积压。

### 16. 业务监控指标（25分钟）

读取/metrics，发10个集群内业务请求再读指标；由于双副本，请固定单Pod观测或在Prometheus按实例sum。手写抓取job或复用Lab10注解发现，验证Content-Type及target up。请求数不等于告警量，不提供延迟P95；要自己新增Histogram才能看分位数。指标label禁用request_id/客户名。

## 第三组：安全周报、存储与恢复

### 17. 周报重复执行（20分钟）

report运行两次，核对created/existing与raw=3/unique=2。记录半开窗口和跨租户过滤；给fixture加一条右边界事件，写离线单测证明进入下个窗口。固定短窗口不是完整周报，生产应由调度参数确定数据版本与时间范围。

### 18. Job失败与重试（25分钟）

从CronJob创建Job的client dry-run导出到work，新增FAIL_REPORT=1，改为独立job名再apply。观察失败Pod数、backoffLimit与Failed condition。修复时建新Job，不能直接修改已创建Job的Pod模板；同时验证退出0但报表错数也必须判失败。

### 19. 定时任务与时区（20分钟）

复制CronJob为独立练习名，schedule改为每分钟、timeZone保持Asia/Shanghai、concurrencyPolicy=Forbid。让任务sleep超过一周期，观察是否并发，再暂停并清理自己创建的任务。手动create job不受同一CronJob的Forbid约束，Forbid不能替代业务幂等。参考security-report保持暂停。

### 20. PVC绑定与数据保留（25分钟）

查询StorageClass、PVC、PV；手写一个独立名称PVC并故意填不存在的storageClassName，观察Pending和Events。删除该错误PVC后用正确清单重建，不尝试修改不可变字段。再重建archive-reader，确认原归档仍存在；本地节点存储不证明节点丢失后数据可恢复。

### 21. 把归档备份到Mac，再恢复到新卷（40分钟）

先report一次，启动只读归档查看Pod与独立恢复Pod：

```bash
kubectl --context kind-labs -n cec-k8s-practice apply -f business/manifests/archive-reader.yaml
kubectl --context kind-labs -n cec-k8s-practice apply -f business/manifests/archive-restore.yaml
kubectl --context kind-labs -n cec-k8s-practice wait --for=condition=Ready pod/archive-reader pod/archive-restore --timeout=90s
mkdir -p business/work
kubectl --context kind-labs -n cec-k8s-practice exec archive-reader -- python -c 'import sys,tarfile; t=tarfile.open(fileobj=sys.stdout.buffer,mode="w|"); t.add("/reports",arcname="reports"); t.close()' > business/work/report-backup.tar
kubectl --context kind-labs -n cec-k8s-practice exec -i archive-restore -- python -c 'import sys,tarfile; t=tarfile.open(fileobj=sys.stdin.buffer,mode="r|*"); t.extractall("/restore",filter="data")' < business/work/report-backup.tar
kubectl --context kind-labs -n cec-k8s-practice exec archive-restore -- python -c 'import pathlib,json; files=list(pathlib.Path("/restore/reports").glob("*.json")); assert files; [print(json.loads(p.read_text())) for p in files]'
```

从两个Pod分别计算报告文件sha256并比较；确认恢复到report-restore而非覆盖report-data。若已有同名Pod但已退出，先删练习Pod再apply。提交源/目标hash、恢复统计、耗时及实际可恢复点。不要删除唯一源卷验证恢复。

## 第四组：权限、隔离与平台场景

### 22. 运维助手最小权限（20分钟）

```bash
kubectl --context kind-labs -n cec-k8s-practice apply -f business/manifests/rbac.yaml
kubectl --context kind-labs auth can-i get configmap/demo-config --as=system:serviceaccount:cec-k8s-practice:cec-demo -n cec-k8s-practice
kubectl --context kind-labs auth can-i get secrets --as=system:serviceaccount:cec-k8s-practice:cec-demo -n cec-k8s-practice
kubectl --context kind-labs auth can-i delete pods --as=system:serviceaccount:cec-k8s-practice:cec-demo -n cec-k8s-practice
```

预期yes/no/no。自己改RoleBinding的subject再观察拒绝。can-i是管理员模拟授权检查；本API没有使用token，不是验证了应用HTTP身份。不能用cluster-admin解决服务账号权限不足。

### 23. 租户配额（25分钟）

在另一个专用namespace `cec-quota-practice` 手写LimitRange/ResourceQuota，限制pods=2、requests.cpu=500m、limits.cpu=1；同时配合合理默认值。创建第3个Pod，保存Quota拒绝输出。配额题不放共享沙箱，以免影响正常发布。结束只删除cec-quota-practice；资源配额不是网络隔离或身份认证。

### 24. 凭据引用（20分钟）

在自己的练习Pod中通过secretKeyRef注入假密码；故意写错key，查CreateContainerConfigError，再修复。检查清单、日志和Git记录均无真实凭据。Secret的base64不是加密，生产还需RBAC、静态加密/外部密钥管理。不要把Secret内容放入capture。

### 25. 服务名与DNS（20分钟）

从API Pod解析monitor-api与monitor-api.cec-k8s-practice.svc.cluster.local；另一个namespace用短名应无法找到该服务，改全名成功。区分NXDOMAIN、解析成功但连接失败、HTTP503；不要为本题修改CoreDNS全局配置。

### 26. 云网平台的域名入口（30分钟，需Controller）

复用Lab07已就绪Ingress Controller，手写Ingress将monitor.demo.test路由到monitor-api:80，ingressClassName按集群实际值。正确Host成功、错误Host不命中该规则；配合Controller日志定位。不要与原实验抢NodePort30080，不能假设Ingress对象创建就自动有入口。

### 27. SOC与监控服务网络隔离（45分钟，独立策略环境）

按Lab13在支持NetworkPolicy的独立CNI环境，创建监控前端、后端、未授权调试Pod，写默认拒绝和最小允许，单独放行DNS。提交允许/拒绝矩阵。默认kind仅接受策略对象而不执行隔离，不能在这里宣称验证通过；不要替换当前labs CNI。

### 28. 专用采集节点（30分钟，独立多节点）

在Lab14 ops集群给一个worker打模拟采集标签/污点，手写nodeAffinity和tolerations；展示“容忍只允许，不保证落到指定节点”。先记录原标签污点，结束恢复。不得给labs唯一节点打污点造成其他练习受影响。

### 29. 维护窗口与PDB（40分钟，独立多节点）

按Lab14两副本与PDB训练，先健康验证再drain一个worker，记录期间Ready数。minAvailable改为全部副本时观察驱逐阻挡，恢复预算后继续维护；最后uncordon。PDB不能防硬故障，不约束Deployment自己的滚动更新。

### 30. 节点日志采集DaemonSet（30分钟，独立多节点）

自己写DaemonSet在两个worker运行busybox心跳，记录节点名；解释控制平面污点。无需挂宿主机敏感目录或开privileged来练调度。生产日志采集还需轮转、缓冲、输出端故障与权限设计，不能用每节点sleep替代真实日志系统。

## 统一验收

每题提交：业务影响一句话、关键字段手写、两条诊断证据、自己的最小修复diff、业务恢复结果、后续预防。80分通过；截图Running而无业务验证不能通过。第一轮优先01–10、17–22，扩展题按依赖完成；未具备Metrics/CNI/多节点环境标未验证。
