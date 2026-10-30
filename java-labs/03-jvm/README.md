# 模块 03：JVM 内存与 GC 调优

> **目标**：理解 JVM 内存模型、GC 算法原理，掌握线上 OOM 排查和性能调优方法
> 
> **面试高频问题**：
> - JVM 内存区域划分及各区域作用？
> - 常见的 GC 算法及适用场景？
> - 线上 OOM 如何排查？
> - 如何选择和调整 GC 参数？

## 包含示例

### 1. MemoryModel.java - JVM 内存模型
演示 JVM 的 5 大内存区域：
- **堆（Heap）**：对象实例，GC 主战场
- **方法区（Method Area）**：类信息、常量、静态变量
- **虚拟机栈（VM Stack）**：方法调用栈，局部变量表
- **本地方法栈（Native Stack）**：Native 方法调用
- **程序计数器（PC Register）**：当前执行指令地址

包含：
- 内存溢出演示（StackOverflow、OutOfMemory）
- 对象内存布局分析
- 运行时数据区可视化

### 2. GCDemo.java - GC 算法演示
演示 4 种垃圾收集算法：
- **Serial GC**：单线程，适合客户端模式
- **Parallel GC**：多线程，吞吐量优先
- **CMS GC**：并发标记清除，低延迟（已废弃）
- **G1 GC**：分区收集，平衡延迟和吞吐量
- **ZGC/Shenandoah**：超低延迟（JDK 11+）

包含：
- GC 日志分析
- 不同 GC 算法性能对比
- GC 调优参数实战

### 3. OOMAnalysis.java - OOM 错误分析
演示 4 种常见 OOM 场景：
- **Java heap space**：堆内存不足
- **GC overhead limit exceeded**：GC 效率过低
- **PermGen/Metaspace**：方法区溢出
- **Direct buffer memory**：直接内存溢出
- **unable to create new native thread**：线程数超限

包含：
- OOM 场景复现
- jmap/jstat/jstack 工具使用
- 堆转储文件分析
- 常见解决思路

## 学习路线

```
1. 先运行 MemoryModel.java，理解内存区域
   ↓
2. 运行 GCDemo.java，对比不同 GC 算法
   ↓
3. 运行 OOMAnalysis.java，学习 OOM 排查
   ↓
4. 阅读源码注释，理解 JVM 调优参数
```

## 常用 JVM 参数速查

```bash
# 堆内存
-Xms512m          # 初始堆大小
-Xmx2048m         # 最大堆大小
-Xmn256m          # 新生代大小

# GC 选择
-XX:+UseSerialGC          # 串行 GC
-XX:+UseParallelGC        # 并行 GC（默认）
-XX:+UseConcMarkSweepGC   # CMS（已废弃）
-XX:+UseG1GC              # G1 GC（推荐）
-XX:+UseZGC               # ZGC（JDK 11+）

# GC 日志
-Xlog:gc*:file=gc.log     # JDK 9+ 统一日志
-XX:+PrintGCDetails -Xloggc:gc.log  # JDK 8

# 调优参数
-XX:NewRatio=2            # 老年代：新生代 = 2:1
-XX:SurvivorRatio=8       # Eden：Survivor = 8:1
-XX:MaxGCPauseMillis=200  # G1 目标停顿时间
-XX:G1HeapRegionSize=4m   # G1 Region 大小

# OOM 时自动 dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/path/to/dump.hprof
```

## 性能监控工具

```bash
# 实时查看 GC 状态
jstat -gcutil <pid> 1000

# 查看堆内存使用
jmap -heap <pid>

# 生成堆转储
jmap -dump:format=b,file=heap.hprof <pid>

# 查看线程栈
jstack <pid>

# 可视化工具
jvisualvm   # JDK 自带
jconsole    # JDK 自带
```

## 调优实战步骤

1. **监控现状**：jstat 查看 GC 频率和耗时
2. **分析问题**：GC 频繁？单次耗时长？内存泄漏？
3. **选择 GC**：根据场景选择（吞吐量 vs 延迟）
4. **调整参数**：堆大小、新生代比例、Region 大小
5. **验证效果**：对比调优前后的 GC 日志
6. **持续监控**：生产环境持续观察

## 推荐阅读

- 《深入理解 Java 虚拟机》周志明
- 《Java 性能优化权威指南》
- [Oracle GC Tuning Guide](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/gctuning/)
