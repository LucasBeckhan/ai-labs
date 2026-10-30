# 🎯 AI 时代大数据架构师 · 全栈学习项目

> **一句话定位**：以"大数据架构师 → AI Infra / AI 平台架构师"为职业主线，
> 覆盖**求职期间需要巩固的全部知识**的一个可运行、可验证、可展示的学习项目。
>
> 全部内容在 `~/Documents/ai-labs/`，所有标注"已验证"的代码都在本机真实运行通过。

## 这个项目解决什么问题

你的现状与目标之间有六条能力缺口，本项目按缺口设计板块：

| # | 缺口 | 对应板块 | 状态 |
|---|---|---|---|
| 1 | AI 方向的核心新技能：**Agent 开发** | [agent-labs/](agent-labs/)（10章业务训练） | 新路线与离线参考已补充 |
| 2 | 云原生底座：**K8s** | [k8s-labs/](k8s-labs/)（14章/30题云网安实战） | 新业务沙箱与故障验证完成 |
| 3 | 模型服务与平台：**AI Infra / LLMOps** | [llmops-labs/](llmops-labs/)（8 个实验） | ✅ 已完成 |
| 4 | 手撕能力：**数据结构与算法** | [algo-labs/](algo-labs/)（10 专题 + 大数据特色题，Java/Python 双解） | ✅ 已完成 |
| 5 | 语言深度：**Java（JVM/并发）+ Python（工程化）** | [java-labs/](java-labs/)、[python-labs/](python-labs/) | ✅ 已完成 |
| 6 | 外企目标：**英语面试（口语）** | [english-labs/](english-labs/)（6 个模块） | ✅ 已完成 |

另有三个横切板块把知识变成 offer：

| 板块 | 作用 | 状态 |
|---|---|---|
| [interview-prep/](interview-prep/) | 175+ 道问答 · 8 场景 · 手撕 SQL · 大厂实践与定级（11 篇） | ✅ 已完成 |
| [career-portfolio/](career-portfolio/) | 把实验产出组装成简历素材与作品集（4 个文档） | ✅ 已完成 |
| [STUDY-GUIDE.md](STUDY-GUIDE.md) + [ROADMAP.md](ROADMAP.md) | 学习方法与 6 个月整合路线 | ✅ 已完成 |

## 项目全景图

```
                        职业主线：大数据架构师 ──→ AI 平台 / AI Infra 架构师
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        ▼             ▼               ▼               ▼             ▼
    ① 语言层       ② 算法层        ③ 大数据层      ④ AI 层        ⑤ 云原生层
   java-labs      algo-labs    interview-prep     agent-labs      k8s-labs
   python-labs                 (02/03/04篇)      llmops-labs     (10 labs)
                                                  (8 labs)       + AI 负载
        │             │               │               │             │
        └─────────────┴───────┬───────┴───────────────┴─────────────┘
                              ▼
                    ⑥ 求职出口层
              english-labs（外企英语）
              interview-prep（问答+场景+谈薪）
              career-portfolio（作品集+简历）
                              │
                              ▼
                     📄 ROADMAP.md —— 6 个月整合路线（每天干什么）
```

## 从哪里开始（三种入口）

1. **不知道学什么** → 读 [ROADMAP.md](ROADMAP.md)（按月/周/日的整合计划）
2. **不知道怎么学** → 读 [STUDY-GUIDE.md](STUDY-GUIDE.md)（五步循环方法论）
3. **马上想动手** → 按 ROADMAP 当周安排进入对应板块，每个实验 README 顶部都有「📖 本章学习指导」

## 已验证内容声明（诚实性）

- **k8s-labs**：14章云网安实战，6次快速路线、30题任务册、9种可注入故障；新增沙箱验证范围见business/VALIDATION.md
- **llmops-labs**：6 个完整验证、Lab07 部分验证（训练）、Lab08 原理篇（无 GPU），含 20 道核心问答
- **agent-labs**：10章云网安业务训练，含手写任务、故障、评估与恢复；新增离线参考通过12例边界测试，完整业务实现需按章练习
- **algo-labs**：10 专题 + 双语言题解 + 大数据特色结构，含 14 道手撕 SQL（实测 PASS）
- **java-labs**：4 模块全部可运行（集合/并发/JVM/函数式），含 20 道核心问答
- **python-labs**：4 模块全部可运行（基础/函数式/并发/数据处理），含 18 道面试题
- **english-labs**：6 模块完整文档（自我介绍/技术问答/行为面试/项目描述/常见问题/发音指南）
- **interview-prep**：175+ 道问答 · 8 场景 · 手撕 SQL · 大厂实践与定级（11 篇，实测数字均来自真实运行）
- **career-portfolio**：4 个文档（简历模板/作品集指南/面试清单/个人品牌），可直接使用
- 引用的外部资料在 interview-prep/README.md 第七节

## 目录清单

```
ai-labs/
├── README.md            # 本文件（总入口）
├── ROADMAP.md           # 6 个月整合路线（求职导向）
├── STUDY-GUIDE.md       # 学习方法论 + 打卡表
├── k8s-labs/            # K8s 云网安实战（14章/30题）
├── llmops-labs/         # LLMOps 八连实验（20 题，已验证）
├── agent-labs/          # 🆕 Agent与Workflow业务训练（10章）
├── algo-labs/           # 🆕 算法专题 + 大数据特色结构（Java/Python 双解，14 题 SQL）
├── java-labs/           # 🆕 Java 深度（集合/并发/JVM/函数式，20 题）
├── python-labs/         # 🆕 Python 工程化（基础/函数式/并发/数据处理，18 题）
├── english-labs/        # 🆕 外企面试英语（6 模块：自我介绍/技术问答/行为面试/项目描述/常见问题/发音指南）
├── career-portfolio/    # 🆕 作品集与简历素材库（4 文档：简历/作品集/面试清单/个人品牌）
└── interview-prep/      # 面试问答手册（11 篇，175+ 题）
```
