# 项目描述 (Project Description)

## 核心框架：PAR 方法

用 PAR 结构描述任何项目（比 STAR 更适合项目介绍）：

### P - Problem（问题/背景）
- 项目要解决什么问题？
- 业务背景是什么？

### A - Approach（方法）
- 你采用了什么技术方案？
- 为什么选择这个方案？

### R - Result（结果）
- 取得了什么成果？（用数字量化）
- 产生了什么影响？

---

## 项目描述模板

### 2 分钟版本

```
I'd like to tell you about [项目名称], which I worked on at [公司].

**Problem**: We faced [问题描述]. For example, [具体例子]. This was costing us 
[量化影响：时间/金钱/用户体验].

**Approach**: I led the technical design and implementation. I chose [技术选择] 
because [原因]. The architecture included [核心组件]. One technical challenge 
was [挑战], which I solved by [解决方案].

**Result**: The project was delivered [时间]. It achieved [量化成果]. The impact 
was [业务影响]. I'm proud of this project because [个人意义].
```

---

## 示例：数据管道项目

```
I'd like to tell you about our real-time data pipeline project at ByteDance.

**Problem**: Our recommendation system was using batch processing with a 6-hour 
delay. Users were seeing outdated recommendations, and we were losing an estimated 
$2M annually in missed engagement opportunities.

**Approach**: I designed a real-time pipeline using Kafka, Flink, and Redis. I 
chose Flink over Spark Streaming because it has lower latency and better exactly-once 
semantics. The architecture included three stages: data ingestion from 20+ microservices, 
real-time feature computation with Flink, and serving through Redis with sub-10ms 
latency. One challenge was handling late-arriving data, which I solved by implementing 
a 5-minute watermark and late data side-output.

**Result**: We delivered the project in 3 months, one month ahead of schedule. It 
reduced data freshness from 6 hours to 30 seconds, improving recommendation accuracy 
by 15%. This increased user engagement by 12%, generating an additional $5M in annual 
revenue. I'm proud of this project because it demonstrated my ability to lead a complex 
technical initiative with significant business impact.
```

---

## 常见问题

### Q: Tell me about a project you're most proud of.
用上面的 PAR 模板回答。

### Q: What was the most technically challenging project you've worked on?
重点突出技术挑战和解决方案。

### Q: Tell me about a project that failed.
诚实描述失败，重点放在学到的教训（参考 challenges.md）。

---

## 练习建议

1. 准备 3-4 个不同的项目故事
2. 每个项目写下来，然后口头练习
3. 确保能在 2-3 分钟内讲完
4. 准备好深入细节（面试官会追问）
