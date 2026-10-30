# Java 深度实验室 (java-labs)

> **目标**：从"会写 Java"到"精通 Java 底层与并发编程"
> **前置**：algo-labs 基础算法完成
> **产出**：4 个模块，16+ 个可运行示例，覆盖集合、并发、JVM、函数式编程

## 为什么需要 Java 深度？

大数据架构师面试中，Java 深度决定你的技术上限：
- **集合框架**：HashMap 的扩容机制、ConcurrentHashMap 的锁分段 → 直接影响分布式系统设计
- **并发编程**：线程池参数调优、锁的选择 → Spark/Flink 任务调度的基础
- **JVM 调优**：GC 算法、内存模型 → 生产环境性能瓶颈排查
- **函数式编程**：Stream API、Lambda → 现代 Java 代码的标配

## 四个模块

### 模块 01：集合框架深度 (01-collections)
- ArrayList vs LinkedList 性能对比
- HashMap 原理（哈希冲突、红黑树、扩容）
- ConcurrentHashMap 分段锁机制
- 面试题：HashMap 为什么线程不安全？

### 模块 02：并发编程 (02-concurrency)
- synchronized vs ReentrantLock
- 线程池核心参数（corePoolSize、maxPoolSize、queue）
- 死锁检测与避免
- 面试题：如何设计一个高并发任务调度器？

### 模块 03：JVM 深度 (03-jvm)
- JVM 内存模型（堆、栈、方法区）
- GC 算法（Serial、Parallel、CMS、G1、ZGC）
- JVM 调优参数实战
- 面试题：线上 OOM 如何排查？

### 模块 04：函数式编程 (04-functional)
- Lambda 表达式与函数式接口
- Stream API 实战（filter、map、reduce）
- Optional 避免空指针
- 面试题：Stream 的并行流何时使用？

## 学习方法

1. **读 README**：每个模块的 README 包含概念讲解和面试题
2. **跑代码**：java/ 目录下的示例可直接编译运行
3. **改参数**：修改代码中的参数，观察行为变化（如线程池大小、GC 算法）
4. **看输出**：每个示例都有详细注释，解释每一步发生了什么

## 目录结构

```
java-labs/
├── README.md
├── 01-collections/
│   ├── README.md
│   └── java/
│       ├── ArrayListVsLinkedList.java
│       ├── HashMapDeepDive.java
│       └── ConcurrentHashMapDemo.java
├── 02-concurrency/
│   ├── README.md
│   └── java/
│       ├── SynchronizedVsLock.java
│       ├── ThreadPoolTuning.java
│       └── DeadlockDetection.java
├── 03-jvm/
│   ├── README.md
│   └── java/
│       ├── MemoryModel.java
│       ├── GCDemo.java
│       └── OOMAnalysis.java
└── 04-functional/
    ├── README.md
    └── java/
        ├── LambdaBasics.java
        ├── StreamAPI.java
        └── OptionalDemo.java
```

## 验证状态

- ✅ 01-collections：3 个示例全部通过
- ✅ 02-concurrency：3 个示例全部通过
- ✅ 03-jvm：3 个示例全部通过
- ✅ 04-functional：3 个示例全部通过

## 相关模块

完成本模块后，可以继续学习：

- **[algo-labs](../algo-labs/)** - 算法面试（Java 实现部分与本模块代码呼应）
- **[python-labs](../python-labs/)** - Python 进阶（对比学习两门语言的并发与函数式特性）
- **[interview-prep](../interview-prep/)** - 面试准备（07-Java 篇与本模块逐节挂钩）
- **[k8s-labs](../k8s-labs/)** - K8s 基础（Java 应用容器化部署依赖 K8s 知识）
- **[agent-labs](../agent-labs/)** - Agent 开发（并发思想相通，但使用 Python）
- **[career-portfolio](../career-portfolio/)** - 职业发展（将 Java 深度能力体现在简历中）

---

**开始学习**：从 [01-collections/README.md](01-collections/README.md) 开始
