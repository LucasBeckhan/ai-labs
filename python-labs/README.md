# Python 深度实验室

> **目标读者**：有编程基础，想深入掌握 Python 高级特性的工程师
> **学习方式**：每个模块包含概念讲解 + 可运行示例 + 面试题

## 四个模块

### 01-basics - Python 基础与数据结构
深入理解 Python 核心机制：
- 可变/不可变对象的内存模型
- 列表推导式与生成器表达式的性能差异
- 字典的哈希表实现与碰撞处理
- 集合的底层原理与高效操作

**面试题**：`is` vs `==`、浅拷贝 vs 深拷贝、GIL 的影响

### 02-functional - 函数式编程与装饰器
掌握 Python 函数式编程范式：
- 一等函数与闭包
- 装饰器原理与多层装饰
- functools 模块（lru_cache, partial, wraps）
- 高阶函数（map, filter, reduce）

**面试题**：装饰器执行顺序、闭包变量捕获、@functools.wraps 的作用

### 03-concurrency - 并发编程
Python 并发模型全景：
- 多线程（threading）与 GIL 限制
- 多进程（multiprocessing）绕过 GIL
- 异步编程（asyncio）事件循环
- 协程 vs 线程 vs 进程的选择

**面试题**：GIL 是什么、asyncio 原理、何时用多进程

### 04-data-processing - 数据处理基础
数据科学入门工具链：
- NumPy 数组操作与广播机制
- Pandas DataFrame 核心操作
- 数据清洗常见模式
- 性能优化技巧

**面试题**：NumPy 广播规则、Pandas merge vs join、向量化 vs 循环

## 学习建议

1. **先读 README**：每个模块的 README.md 包含核心概念和面试题
2. **运行示例**：每个 `.py` 文件都可独立运行，观察输出
3. **修改实验**：改动代码参数，理解行为变化
4. **完成练习**：每个模块末尾有练习题，检验理解程度

## 环境要求

- Python 3.8+
- 标准库（无需安装）
- 模块 04 需要：`pip install numpy pandas`

## 验证状态

- ✅ 01-basics：3 个示例全部通过
- ✅ 02-functional：3 个示例全部通过
- ✅ 03-concurrency：3 个示例全部通过
- ✅ 04-data-processing：3 个示例全部通过

## 相关模块

完成本模块后，可以继续学习：

- **[algo-labs](../algo-labs/)** - 算法面试（Python 实现部分与本模块代码呼应）
- **[java-labs](../java-labs/)** - Java 进阶（对比学习两门语言的并发与函数式特性）
- **[interview-prep](../interview-prep/)** - 面试准备（算法和系统设计篇与本模块呼应）
- **[llmops-labs](../llmops-labs/)** - LLM 应用开发（本模块是 Lab 03-06 的前置）
- **[agent-labs](../agent-labs/)** - Agent 开发（本模块是 Lab 01-08 的前置）
- **[career-portfolio](../career-portfolio/)** - 职业发展（将 Python 能力体现在简历中）
