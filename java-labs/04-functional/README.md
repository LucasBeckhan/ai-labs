# 模块 04：函数式编程

> **目标**：掌握 Java 8+ 函数式编程特性，写出简洁、可维护的现代 Java 代码
> 
> **面试高频问题**：
> - Lambda 表达式和匿名内部类的区别？
> - Stream API 的中间操作和终端操作有哪些？
> - 并行流什么时候用？有什么风险？
> - Optional 如何避免空指针？

## 包含示例

### 1. LambdaBasics.java - Lambda 表达式基础
演示 Lambda 的核心概念：
- 函数式接口（@FunctionalInterface）
- Lambda 语法演进（匿名类 → Lambda → 方法引用）
- 常用内置函数式接口（Predicate、Function、Consumer、Supplier）
- 闭包与变量捕获（effectively final）

包含：
- 语法对比示例
- 自定义函数式接口
- 方法引用的 4 种形式

### 2. StreamAPI.java - Stream API 实战
演示 Stream 的完整流水线：
- **创建流**：集合、数组、Stream.of()、Stream.generate()
- **中间操作**：filter、map、flatMap、distinct、sorted、limit、skip
- **终端操作**：forEach、collect、reduce、count、min/max、anyMatch/allMatch
- **并行流**：parallelStream()、性能对比、线程安全问题

包含：
- 数据处理流水线示例
- 收集器（Collectors）使用
- 性能基准测试

### 3. OptionalDemo.java - Optional 最佳实践
演示 Optional 的正确用法：
- 创建：Optional.of()、Optional.ofNullable()、Optional.empty()
- 获取：get()、orElse()、orElseGet()、orElseThrow()
- 链式：map()、flatMap()、filter()
- 常见反模式（避免 isPresent() + get()）

包含：
- 空值处理对比
- 链式调用示例
- 实际业务场景

## 学习路线

```
1. 先运行 LambdaBasics.java，理解 Lambda 语法
   ↓
2. 运行 StreamAPI.java，掌握流式处理
   ↓
3. 运行 OptionalDemo.java，学会空值处理
   ↓
4. 阅读源码注释，理解函数式编程思想
```

## 核心概念

### 1. Lambda 表达式本质
```java
// Lambda 是匿名函数，可以赋值给变量、作为参数传递
Comparator<Integer> comp = (a, b) -> a - b;

// 本质：实现了函数式接口的唯一抽象方法
@FunctionalInterface
interface MyFunction {
    int apply(int x);
}
MyFunction square = x -> x * x;
```

### 2. Stream 操作分类
| 类型 | 特点 | 示例 |
|------|------|------|
| 中间操作 | 返回 Stream，可链式调用 | filter, map, sorted |
| 终端操作 | 返回结果，触发执行 | collect, count, forEach |
| 短路操作 | 找到结果就停止 | anyMatch, findFirst |

### 3. 并行流注意事项
```java
// 适合：CPU 密集型、数据量大、无状态操作
long count = list.parallelStream()
    .filter(x -> x > 0)
    .count();

// 不适合：IO 密集型、有状态操作、小数据量
// 风险：线程切换开销、共享变量竞争
```

## 性能对比

### Lambda vs 匿名类
- Lambda：编译时生成 invokedynamic 指令，运行时由 JVM 优化
- 匿名类：编译时生成独立 .class 文件，加载开销大
- 性能差异：Lambda 快 2-5 倍（取决于 JVM 优化）

### 串行流 vs 并行流
- 数据量 < 10000：串行流更快（避免线程切换开销）
- 数据量 > 100000：并行流更快（多核加速）
- 临界点：取决于 CPU 核心数、操作复杂度

## 最佳实践

### 1. Lambda 使用原则
```java
// ✓ 推荐：简洁明了
list.forEach(item -> process(item));

// ✗ 避免：过于复杂，改用方法
list.forEach(item -> {
    if (item.isValid()) {
        process(item);
        log.info("Processed: " + item);
    }
});
```

### 2. Stream 使用原则
```java
// ✓ 推荐：链式调用，一气呵成
List<String> result = list.stream()
    .filter(s -> s.length() > 5)
    .map(String::toUpperCase)
    .sorted()
    .collect(Collectors.toList());

// ✗ 避免：中间变量，破坏流式风格
Stream<String> stream = list.stream();
stream = stream.filter(s -> s.length() > 5);
stream = stream.map(String::toUpperCase);
List<String> result = stream.collect(Collectors.toList());
```

### 3. Optional 使用原则
```java
// ✓ 推荐：链式调用
String name = Optional.ofNullable(user)
    .map(User::getName)
    .orElse("Unknown");

// ✗ 避免：isPresent + get（和 if-else 没区别）
String name;
if (userOptional.isPresent()) {
    name = userOptional.get().getName();
} else {
    name = "Unknown";
}
```

## 面试题精选

**Q1：Lambda 和匿名内部类的区别？**
```
1. 编译产物：Lambda 生成 invokedynamic 指令，匿名类生成 .class 文件
2. this 指向：Lambda 指向外部类，匿名类指向自身
3. 变量捕获：Lambda 只能访问 effectively final 变量
4. 性能：Lambda 更快（JVM 优化）
```

**Q2：Stream 的中间操作和终端操作？**
```
中间操作（惰性求值，返回 Stream）：
  - filter、map、flatMap
  - distinct、sorted
  - limit、skip
  - peek（调试用）

终端操作（触发执行，返回结果）：
  - forEach、forEachOrdered
  - collect、toArray
  - reduce
  - count、min、max
  - anyMatch、allMatch、noneMatch
  - findFirst、findAny
```

**Q3：并行流的风险？**
```
1. 线程安全问题：共享变量竞争（避免在 lambda 中修改外部变量）
2. 性能开销：线程切换、任务拆分合并（小数据量反而更慢）
3. 顺序问题：forEach 不保证顺序，用 forEachOrdered
4. 副作用：有状态的 lambda 在并行下行为不可预测
```

**Q4：Optional 的正确用法？**
```
✓ 推荐：
  - orElse(defaultValue)
  - orElseGet(() -> defaultValue)
  - orElseThrow(() -> new Exception())
  - map/flatMap 链式调用

✗ 避免：
  - isPresent() + get()（和 null 检查没区别）
  - 作为字段类型（不可序列化）
  - 作为方法参数（增加调用方复杂度）
```

## 扩展阅读

- 《Java 8 实战》（Raoul-Gabriel Urma）
- [Oracle Stream API 文档](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html)
- [Baeldung Java 8 教程](https://www.baeldung.com/java-8-streams)
