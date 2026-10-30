# 模块 01：集合框架深度

> **核心问题**：Java 集合框架的底层实现决定了你的代码性能
> **学习目标**：理解 List/Set/Map 的底层数据结构，能在生产环境选择正确的集合类型

## 三个核心示例

### 1. ArrayListVsLinkedList.java
**对比 ArrayList 和 LinkedList 的性能差异**
- 随机访问：ArrayList O(1) vs LinkedList O(n)
- 头部插入：ArrayList O(n) vs LinkedList O(1)
- 尾部插入：两者都是 O(1)（均摊）

**面试题**：
- "什么时候用 LinkedList？" → 频繁在头部/中间插入删除，且不需要随机访问
- "ArrayList 扩容机制？" → 每次扩容 1.5 倍，System.arraycopy 复制

### 2. HashMapDeepDive.java
**深入 HashMap 的底层实现**
- 哈希冲突解决：链表 + 红黑树（JDK 8+）
- 扩容机制：容量翻倍，rehash 所有节点
- 线程不安全：并发 put 导致死循环（JDK 7）或数据丢失（JDK 8）

**面试题**：
- "HashMap 为什么用红黑树？" → 链表长度 > 8 时，查找从 O(n) 优化到 O(log n)
- "HashMap 的容量为什么是 2 的幂？" → (n-1) & hash 等价于取模，但位运算更快

### 3. ConcurrentHashMapDemo.java
**理解 ConcurrentHashMap 的线程安全机制**
- JDK 7：分段锁（Segment，默认 16 个段）
- JDK 8：CAS + synchronized（锁粒度从段降到桶）
- size() 方法：baseCount + CounterCell[]（类似 LongAdder）

**面试题**：
- "ConcurrentHashMap 的 size() 如何保证准确？" → baseCount + CounterCell[]，失败时重试
- "为什么不用 HashTable？" → HashTable 全表锁，并发度只有 1

## 运行方式

```bash
cd java-labs/01-collections/java
javac *.java
java ArrayListVsLinkedList
java HashMapDeepDive
java ConcurrentHashMapDemo
```

## 关键知识点

### 1. List 选择
| 场景 | 推荐 | 原因 |
|------|------|------|
| 随机访问多 | ArrayList | O(1) 访问 |
| 头部插入多 | LinkedList | O(1) 插入 |
| 尾部插入多 | ArrayList | 均摊 O(1)，缓存友好 |

### 2. Map 选择
| 场景 | 推荐 | 原因 |
|------|------|------|
| 单线程 | HashMap | 最快 |
| 多线程 | ConcurrentHashMap | 高并发 |
| 需要排序 | TreeMap | 红黑树实现 |

### 3. Set 选择
- HashSet：底层是 HashMap（value 是虚拟对象）
- TreeSet：底层是 TreeMap
- LinkedHashSet：维护插入顺序

## 面试题精选

**Q1：HashMap 的 put 流程？**
```
1. 计算 hash，定位桶
2. 桶为空 → 直接插入
3. 桶不为空 → 遍历链表/红黑树
   - key 相同 → 覆盖 value
   - key 不同 → 插入链表尾部（尾插法，JDK 8+）
4. 链表长度 > 8 → 转红黑树
5. size > threshold → 扩容（2 倍）
```

**Q2：ConcurrentHashMap 的 get 为什么不用加锁？**
- 读操作不加锁，通过 volatile 保证可见性
- Node 的 val 和 next 是 volatile
- sizeCtl 用 CAS 保证原子性

**Q3：为什么 HashMap 的容量必须是 2 的幂？**
- 索引计算：(n-1) & hash
- 如果 n 是 2 的幂，n-1 的二进制全是 1，& hash 等价于取模
- 位运算比取模快 10 倍以上

## 扩展阅读

- 《Java 并发编程实战》第 5 章：构建块
- HashMap 源码分析：关注 resize() 和 treeifyBin()
- ConcurrentHashMap 源码分析：关注 transfer() 和 addCount()
