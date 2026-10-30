# 07 — Java / JVM / 计算机基础 20 题（大数据岗的一面隐形门槛）

> 大数据开发岗一面必夹带 Java 基础与计算机基础——因为 Spark/Flink/Kafka 全是 JVM 生态，JVM 调优和引擎调优是一体的。这部分的策略：**不追求 Java 专家深度，但要能从"写 Java 的人"升级为"调 JVM 的人"**。每题同样带【追问链】。

## A. Java 集合与并发（6 题）

### Q1. ★ HashMap 的底层原理？1.7 和 1.8 的区别？为什么线程不安全？

【参考回答】1.8 结构：数组 + 链表 + 红黑树。put 流程：hash 扰动（高 16 位异或，让高位参与运算减少碰撞）→ `(n-1) & hash` 定位桶 → 链表尾插（1.7 头插在并发扩容会成环死循环，1.8 改尾插但仍线程不安全——数据覆盖丢失）→ 链表长度 ≥8 且数组长度 ≥64 树化（否则先扩容）。扩容：容量翻倍，1.8 优化为**按 hash & oldCap 拆高低位链表**，无需重算 hash。默认容量 16、负载因子 0.75（泊松分布下桶冲突概率与时空成本的折中）。

【追问链】为什么容量是 2 的幂？（位运算取模 + 扩容拆分）→ 线程安全用什么？（ConcurrentHashMap：1.8 CAS + synchronized 锁单个桶头节点，锁粒度从 1.7 的分段锁变桶级）→ 试试说 red-black 树退化的情况？（节点删除到 6 退化回链表）

### Q2. ★ 线程池的核心参数与执行流程？大数据组件里哪里用到了？

【参考回答】七参数：corePoolSize、maximumPoolSize、keepAliveTime、workQueue、threadFactory、rejectedHandler（+ unit）。执行顺序（高频坑题）：**先填 core → 队列 → 再扩到 max → 再触发拒绝**——不是"先扩满再入队"。拒绝策略四种：Abort（抛异常）/CallerRuns（调用者执行，反压思想）/Discard/DiscardOldest。**大数据连接**：Flink 的 mailbox 线程模型、Spark 的 RPC 环境、Kafka network layer——都遵循"业务线程与 IO 线程分离 + 有界队列反压"的思想；自己写 Flink RichFunction 里开线程池做异步 IO 时，CallerRuns 就是天然的限流。

【追问链】怎么合理设置线程数？（CPU 密集 = N+1；IO 密集 = N × (1 + 等待/计算)，用压测校准）→ 无界队列的风险？（内存溢出 + 任务延迟不可控——Flink 反压本质就是这个问题的分布式版）

### Q3. ThreadLocal 原理与内存泄漏？

【参考回答】每个 Thread 持有 ThreadLocalMap，key 是 ThreadLocal 的弱引用、value 是强引用——线程池场景线程长存，value 不回收就泄漏，所以 **finally 里必须 remove()**。大数据场景：SimpleDateFormat 这类非线程安全对象用 ThreadLocal 复用（比每次 new 快），Flink 的 RichFunction open() 里初始化就是同样思想。

### Q4. volatile 和 synchronized 的区别？happens-before 是什么？

【参考回答】volatile：可见性（写立即刷主存、读失效缓存行）+ 禁止指令重排（内存屏障），**不保证原子性**（i++ 仍会丢更新）；synchronized：原子性 + 可见性，锁对象头（偏向/轻量级/重量级锁升级）。happens-before 是 JMM 的偏序规则：程序顺序、monitor 锁、volatile 写读、线程 start/join 等——判断有没有并发 bug 的理论工具。**数据连接**：Spark/Flink 源码里大量 volatile 状态位（如 task 状态），问这个是看你会不会读源码。

### Q5. Java 中什么叫不可变对象？为什么 Flink/Spark 的配置对象要设计成不可变？

【参考回答】创建后状态不可改（final 字段 + 不提供 setter + 防御性拷贝）。好处：天然线程安全、可自由共享缓存。**引擎视角**：Spark 的 SparkConf/Flink 的 ParameterTool 一旦构建就只读——因为任务序列化分发到所有 executor 后，配置必须全员一致，可变对象会导致"节点间配置漂移"这种极难排查的 bug。

### Q6. 接口和抽象类？函数式接口和 Lambda 的本质？

【参考回答】接口是"能做什么"的契约（多实现），抽象类是"是什么"的模板复用（单继承 + 可有状态）。Lambda 本质是函数式接口的实例（语法糖），编译后是 invokedynamic + 合成方法。**大数据连接**：Spark 的 transformation 全是 Lambda/函数对象——要理解闭包序列化（Task not serializable 报错的原因：闭包捕获了不可序列化的外部对象），这是 Spark 开发最常见报错，答 Java 基础时主动带到这层很加分。

## B. JVM（7 题，与引擎调优直接挂钩）

### Q7. ★ JVM 内存区域划分？哪些会 OOM？

【参考回答】线程共享：**堆**（对象，OOM: Java heap space）、**元空间 Metaspace**（类元数据，本地内存，OOM: Metaspace——动态生成类过多触发，如 Groovy/CGLIB）；线程私有：虚拟机栈（StackOverflowError——递归过深）、本地方法栈、程序计数器。**数据岗挂钩**：executor 的 137 里，堆 OOM（GC 后仍不够）、元空间 OOM、堆外（Direct memory / Netty）三种死法要能区分——对应 -Xmx / -XX:MaxMetaspaceSize / -XX:MaxDirectMemorySize 三个参数。

【追问链】堆外内存怎么监控？（NMT -XX:NativeMemoryTracking + Netty 指标；容器里更要看 cgroup 层的 RSS）→ 为什么 Spark 3 建议 UnifiedMemoryManagement？不要把问题停留在概念（见 03 篇 Q2 的统一内存模型）

### Q8. ★ 对象什么时候进老年代？G1 和 CMS 的区别？大数据作业选哪个？

【参考回答】进老年代：年龄到阈值（默认 15）、大对象直接进（G1 按 region 判定）、动态年龄判断（同龄对象总和超 survivor 一半）。**CMS**：并发标记清除，低停顿但**内存碎片**（无压缩）+ 并发失败退化 Full GC；**G1**：Region 化 + 可预测停顿（-XX:MaxGCPauseMillis），混合回收，JDK9+ 默认。**大数据作业选型**：长生命周期大堆（executor 8G+、Flink 状态多）选 **G1 或 ZGC**；CMS 已淘汰。实战：Spark executor 从默认 Parallel GC 换 G1 后，单次 GC 停顿从 800ms 降到 50ms 内，长任务尾延迟显著下降——这是能进简历的 JVM 调优。

【追问链】GC 日志怎么看？给一个排查案例？（`-Xlog:gc*`，看停顿分布与回收效果；案例：某作业周期性长停顿，发现是大对象直接进老年代，调 -XX:G1HeapRegionSize 解决）→ ZGC 什么时候用？（超大堆 + 亚毫秒停顿要求，如常驻 Flink JobManager）

### Q9. Full GC 频繁怎么排查？（框架化回答）

【参考回答】五步：① `jstat -gcutil` 看各代水位与频率 → ② 判断触发原因（老年代满/元空间满/System.gc()/ promotion failed）→ ③ dump 分析（`jmap -dump` + MAT 看 dominator tree——谁占着老年代）→ ④ 常见根因：缓存无界（cache 无淘汰）、大集合一次加载（Spark 读大维度表 driver OOM 同源）、内存泄漏（ThreadLocal/监听器）、堆太小 vs 数据量真实增长 → ⑤ 治理：代码修复 + 参数调整 + 告警（GC 停顿百分位）。

【追问链】线上不能 dump 怎么办？（jstat + jmap -histo 活对象直方图轻量分析；重启前留 dump）→ 大数据作业里 Full GC 多的典型业务原因？（窗口/缓存数据量随业务增长，容量规划没跟上——治理思路同 03 篇 Q12 Flink 状态）

### Q10. 类加载过程与双亲委派？为什么 Spark/Flink 要打破它？

【参考回答】加载 → 验证 → 准备 → 解析 → 初始化；双亲委派：子加载器先委托父加载器（防止核心类被篡改 + 避免重复加载）。**打破场景**：Spark/Flink 的 **user classpath 与框架 classpath 隔离**——用户 jar 里的依赖版本和框架不同（同一 Kafka client 两个版本共存），必须用独立 ClassLoader（如 `spark.executor.userClassPathFirst`，或 Flink 的 child-first 默认策略）。这题答到"为什么打破"就是数据岗的正确姿势——**jar 包冲突是大数据开发的第一大痛**。

【追问链】NoClassDefFoundError 和 ClassNotFoundException 区别？（前者：编译期有、运行期加载失败/初始化失败——典型 jar 冲突；后者：运行期显式加载找不到）

### Q11. 强软弱虚四种引用？

【参考回答】强（GC 不回收）→ 软（内存不足才回收，适合缓存）→ 弱（下次 GC 必回收，ThreadLocalMap 的 key）→ 虚（跟踪回收过程，Cleaner/堆外内存释放——**DirectByteBuffer 的堆外内存就是靠虚引用 + Cleaner 释放的**，这就是为什么堆外 OOM 难排查：释放依赖 GC）。

### Q12. JVM 调优的实际案例怎么讲？

【参考回答】模板：现象（GC 频率/停顿数字）→ 假设（水位分析）→ 动作（参数 + 代码）→ 前后对比 → 沉淀。示例：某 Flink 作业每隔 20 分钟一次 1.2s 的 GC 停顿导致反压；分析发现老年代被大批量对象填充（窗口聚合临时对象），改 G1 + `MaxGCPauseMillis=100` + 算子内对象复用，停顿降到 80ms 内、反压消失。**面试官验证你真实性的方式就是追问具体数字与参数名**。

## C. 计算机网络与 OS（5 题）

### Q13. TCP 三次握手为什么不能两次？四次挥手为什么需要 TIME_WAIT？

【参考回答】三次：防止历史失效的连接请求突然到达（两次会让服务端误建连接浪费资源）+ 同步双方初始序列号。四次：半关闭（一方发完数据仍可收）；TIME_WAIT（主动关闭方等 2MSL）：① 保证最后一个 ACK 若丢失、对端重传 FIN 时还能应答；② 让旧连接的报文在网络中自然消亡，不污染新连接。**工程连接**：大量 TIME_WAIT（爬虫/网关场景）用连接池复用解决——这也是为什么 Kafka/Spark RPC 都强依赖长连接池。

### Q14. 零拷贝是什么？Kafka 哪里用了？

【参考回答】传统读文件发网络：磁盘 → 内核缓冲 → 用户态 → Socket 缓冲 → NIC，4 次拷贝 4 次上下文切换。零拷贝（sendfile）：数据直接从页缓存到 NIC，省 2 次拷贝 2 次切换。Kafka consumer 拉取消息走 sendfile；**限制**：需要 TLS 加密时不能用 sendfile（数据要过用户态加密）——这就是"开 SSL 后 Kafka 吞吐下降"的原因之一，能把这点讲出来非常加分。

### Q15. IO 多路复用？select/poll/epoll 的区别？

【参考回答】select（fd 数组，1024 上限，每次全量遍历）→ poll（链表无上限，仍全量遍历）→ **epoll**（红黑树注册 + 就绪链表回调，O(1) 事件通知，边缘/水平触发）。Kafka/Netty/Nginx 全靠 epoll。**连接**：Flink 的 webUI 和 netty shuffle 层、Kafka broker 的网络线程模型（acceptor + processor + handler 分层）都基于此——面试常让你"用 epoll 解释 Kafka 网络层为什么单机能扛几十万连接"。

### Q16. 进程、线程、协程的区别？大数据组件里对应什么？

【参考回答】进程（独立地址空间）→ 线程（共享地址空间，内核调度，切换成本 = 上下文切换 + 缓存失效）→ 协程（用户态调度，切换纳秒级）。对应：Spark executor 是进程，里面 task 是**线程**（所以 executor 内存全局共享、task 间会互相影响——这也是"一个倾斜 task 拖死同 executor 其他 task"的原因）；Flink 也是进程内多线程跑 subtask；Go/协程思想最近进了 Flink（虚拟线程 Loom 也在 JVM 落地中）。

### Q17. 什么是 mmap？Spark/Flink 哪里用到了？

【参考回答】mmap 把文件映射进虚拟地址空间，读写像访问内存。用途：Spark shuffle 的索引文件读取、Flink RocksDB 依赖 OS page cache、Kafka 索引文件 mmap——本质都是"少一次拷贝 + 借用页缓存"。回答时点一句"这就是为什么 shuffle 索引损坏表现为越界异常"即可。

## D. 设计与工程素养（3 题）

### Q18. 单例模式的几种写法？Flink/Spark 里哪里是单例思想？

【参考回答】双重检查锁（volatile + 两次判空）、静态内部类（懒加载 + 线程安全，推荐）、枚举（防反射反序列化）。引擎里：SparkContext/StreamExecutionEnvironment 本质是进程内单例；Flink 的 MetricsRegistry、各类 plugin manager。**追问预警**：为什么静态内部类能懒加载？（类加载机制：内部类首次使用才加载，由 JVM 保证线程安全——比双重检查锁干净）

### Q19. 你在项目里做过最有价值的一次代码重构/抽象？

【参考回答】模板（数据岗专属）：**把重复逻辑沉淀成平台能力**。示例：十几个 Spark 作业各自手写"读 Kafka → 清洗 → 去重 → 写湖"，抽象成统一的"入湖作业模板"（配置驱动：表名/主键/merge 引擎），新业务接入从 2 天降到 30 分钟配置，且去重规则 bug 只需要修一处。**面试官在听**：抽象的判断标准（什么时候该抽象——重复 ≥3 次且语义稳定）、抽象后的推广方式（模板 + 文档 + 强制走平台）。

### Q20. 看过什么源码？讲一条你印象最深的调用链。

【参考回答】40k 档"看过源码"要能讲出**具体的类名与设计决策**，以下三条任选你真看过的：
- **Spark ShuffleMapTask → SortShuffleWriter → BypassMergeSortShuffleWriter**（task 数 ≤200 时绕过排序直接分文件——`spark.shuffle.sort.bypassMergeThreshold`，回答"小作业 shuffle 为什么不慢"）
- **Flink CheckpointCoordinator → 触发 barrier → StateBackend snapshot 异步线程**（解释"为什么 checkpoint 大也不影响吞吐"——异步快照 + 写时复制）
- **Kafka ReplicaManager → ISR 收缩/扩张**（结合 Q17 的 acks 语义）
**诚实原则**：说"我读过这条链路的实现"比"我读透了整个项目"可信一百倍。

---

# 深挖补充（防问倒版）

## 深挖 1：G1 回收全流程与大数据作业的参数表

**G1 基本结构**：堆划成 2048 个左右等大 Region（1~32MB）；Eden/Survivor/Old 都是 Region 的逻辑集合，Humongous（≥ Region 一半的对象）独占连续 Region。

**两种回收**：
- **Young GC**：Eden 满触发，STW，存活对象复制到 Survivor/Old——停顿与 Eden 存活对象量成正比；
- **Mixed GC**：老年代占比达 **IHOP**（InitiatingHeapOccupancyPercent，默认 45%）→ 并发标记周期（初始标记搭车 Young GC → 并发标记 → 最终标记 → 清理）→ 之后若干次 Young GC 顺带回收"垃圾比例高的老年代 Region"（这就是 Mixed）。

**大数据作业参数表**（executor 8G 堆示例）：
```
-XX:+UseG1GC
-XX:MaxGCPauseMillis=100          # 目标停顿，G1 会自适应调整 young region 数
-XX:G1HeapRegionSize=16m          # 防止大对象（缓存块/shuffle页）成为 Humongous
-XX:InitiatingHeapOccupancyPercent=40   # 老年代占比提前触发并发标记，留余量
-XX:G1ReservePercent=15           # 预留to-space，防晋升失败(Evacuation Failure)
-Xlog:gc*:file=gc.log             # 必开，排障的原始证据
```
**典型事故复盘表述**：某长任务周期性 1.5s 停顿 → GC 日志显示 Humongous Allocation 频繁 + Evacuation Failure → 根因是 cache 的 32MB 块对象超过默认 region 2MB → RegionSize 调 16m + 缓存块拆小 → 停顿降到 60ms。

**追问实录**："为什么不用 ZGC？" 答：ZGC 停顿 <1ms 但吞吐换停顿（着色指针屏障开销 ~10%）；离线批处理吞吐优先，G1 均衡；常驻低延迟服务（如实时网关 JVM）才值得 ZGC。

## 深挖 2：线程池参数的量化推导（面试现场能算）

以 Flink sink 写 JDBC 为例：sink 并行度 4，每个 task 处理 1000 条/s，单条 JDBC 写 5ms。
- 理论：每 task 需要 1000 × 0.005 = 5 个并发连接/线程才能跟上流速；
- 连接池 = task 线程数 × 每线程并发数；DB 总连接 = 4 × 5 = 20 —— **先算 DB 侧容量再定并行度**，顺序反了就是打挂 DB 的事故。
- 线程池队列：有界（如 1000）+ CallerRunsPolicy——背压传导到 Flink 算子，反压是特性不是缺陷。

## 深挖 3：ConcurrentHashMap 1.8 的 put 全流程（被追问到底层）

1. 计算 hash（spread：高 16 位异或）；
2. 桶为空 → **CAS** 放入（无锁成功即返回）；
3. 桶头是 ForwardingNode（正在扩容）→ **协助扩容**（helpTransfer）；
4. 否则 **synchronized 锁桶头节点** → 链表尾插 / 红黑树插入；
5. binCount 达到 TREEIFY_THRESHOLD → 检查数组长度 ≥64 否则扩容（树化前提）；
6. addCount：CAS 更新 baseCount + CounterCell 数组（分散热点）→ 检查是否需要扩容（多线程协同迁移，stride = n>>>3 / NCPU 最小 16）。
**金句**：1.8 的 CHM = CAS（空桶）+ synchronized（非空桶）+ 多线程协同扩容——三把刀都用在了刀刃上。

## 深挖 4：epoll 的 LT/ET 与 Kafka 网络层的对应

- **LT（水平触发）**：只要缓冲区有数据就一直通知——编程简单，可能重复唤醒；
- **ET（边缘触发）**：状态变化才通知一次——必须一次读/写到位（循环 read 到 EAGAIN），高效但易饿死。
- **Kafka 网络层映射**：Acceptor（1 个，接收连接）→ Processor（N 个，跑 selector 处理读写——ET 模式 + 队列）→ Handler（K 线程，真正处理请求）——"连接与处理分离"让它单机扛数万连接且延迟可控。**追问预警**："为什么 Handler 不直接做 IO？"（IO 阻塞会拖住事件循环，所有连接排队——分层是隔离慢与快）。
