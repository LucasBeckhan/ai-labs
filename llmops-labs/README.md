# LLMOps / AI Infra 实验室 —— 人人可学的大模型工程路线

> 前置：建议先完成 [k8s-labs](../k8s-labs/)（容器、K8s 核心对象、调度、存储、HPA、监控、Spark on K8s）。
> 本仓库回答一个问题：**有了基础的编程与 K8s 能力，如何系统地掌握 LLMOps / AI Infra？**
> 所有实验同样在本机（Apple Silicon 16GB，无 GPU、无外网 VPN）实际验证过，验证状态见各实验文档与文末总表。

> 📖 **不知道从哪开始学？先读根目录的 [STUDY-GUIDE.md](../STUDY-GUIDE.md)** —— 12 周学习路线、每章学习卡片、破坏练习与验收自测。

## 零基础怎么开始

1. **先读 [GLOSSARY.md](GLOSSARY.md)** 混个脸熟：token、量化、RAG、网关……后面到处都是
2. **自检前置**：会 Python 基本语法、能看懂 curl 命令、已完成 k8s-labs（或至少 Lab 01/02/07）
3. **从 Lab 01 开始按顺序做**；Lab 02 之后的生成请求都走 Lab 02 的网关，别跳
4. 每个 lab 的 `knowledge/`、`setup/` 都是可替换的：换成你自己的文档和数据库，学得更快
5. 卡住了去对应实验的「常见坑」找 —— 全部是本机真实踩过的坑

## 一、先看清地图：LLMOps / AI Infra 到底做什么

| 层 | 干什么 | 典型组件 | 学习重心 |
|---|---|---|---|
| **模型层** | 训练/微调/量化，产出可服务的模型 | PyTorch、LoRA/QLoRA、vLLM/SGLang、MLX | 训练工程化：数据格式、评估、防过拟合 |
| **推理服务层** | 把模型变成高吞吐低延迟的 API | vLLM（PagedAttention/连续批处理）、KServe、Triton | 吞吐与延迟、显存管理、K8s 部署 |
| **应用编排层** | RAG、Agent、工作流，把模型接进业务 | LangChain/LlamaIndex、向量库、MCP | 检索质量、数据质量、SQL 与业务连接 |
| **平台运维层** | 多模型路由、配额/成本、观测、评估 | LiteLLM、Prometheus、OpenTelemetry、评估流水线 | 路由、限流、预算、监控、CI/CD |

**学习路线建议：应用编排层（RAG/Agent）→ 平台运维层（网关/观测/评估）→ 推理服务层（vLLM 原理）→ 模型层（LoRA 入门）**。前两层偏工程、上手快；后两层需要补机器学习工程知识。

## 二、实验路线（建议 6~8 周，每周 5~8 小时）

| # | 实验 | 学什么 | 前置 | 验证状态 |
|---|---|---|---|---|
| [Lab 01](lab01-local-llm/) | 本地跑通开源模型 + OpenAI 兼容 API | 模型/量化/上下文窗口/token 的体感；推理参数 | K8s Lab 01 | ✅ 已验证 |
| [Lab 02](lab02-litellm-gateway/) | LiteLLM 网关：统一接入与成本观测 | 生产级 AI 网关：模型路由、虚拟 key、预算、日志 | Lab 01 | ✅ 已验证 |
| [Lab 03](lab03-rag-basics/) | RAG 基础：用**你自己的文档**建知识库 | 分块/嵌入/向量库/检索增强全链路 | Lab 01 | ✅ 已验证 |
| [Lab 04](lab04-rag-eval/) | RAG 评估：没有评估就没有 LLMOps | 评估集构建、检索命中率、忠实度 | Lab 03 | ✅ 已验证 |
| [Lab 05](lab05-text2sql-agent/) | Text2SQL Agent：让大模型查你的数据库 | 工具调用/函数 Calling、SQL 安全护栏 | Lab 01 | ✅ 已验证 |
| [Lab 06](lab06-ai-platform/) | 毕业项目：Mini AI 平台上 K8s | 网关+RAG 服务容器化、Ingress、Prometheus 监控 token 消耗 | Lab 02/03 + K8s 全部 | ✅ 已验证 |
| [Lab 07](lab07-finetune-intro/) | LoRA 微调入门 | 微调的工程流程：数据格式/训练/评估 | Lab 01 | ⚙️ 部分验证（见文档说明） |
| [Lab 08](lab08-gpu-inference-prod/) | GPU 推理生产化（原理篇） | vLLM 原理、GPU 调度、显存管理、时间片 | K8s Lab 06 | 📖 原理篇（本机无 GPU） |

## 三、环境准备（一次性）

```bash
# 1. Ollama（Apple Silicon 原生跑开源模型，走 Metal 加速，不占 Docker 虚拟机内存）
brew install ollama
ollama serve &                       # 或 brew services start ollama
ollama pull qwen2.5:0.5b-instruct    # 约 400MB，中文友好

# 2. Python 虚拟环境（已内置在本仓库 .venv；换了机器重跑下面两行）
python3 -m venv .venv
.venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ "litellm[proxy]" pymysql chromadb ollama prisma
```

**国内网络要点**（本机实测）：Hugging Face 需要走镜像 —— 训练/嵌入模型下载前设置 `export HF_ENDPOINT=https://hf-mirror.com`；pip 用阿里云源（清华源对部分 wheel 返回 403，实测踩过）；Ollama 模型源国内可直连。

## 四、这 8 个实验构成的能力地图

1. **Lab 01/02/06 构成"AI 平台"故事线**：模型服务 → 统一网关（多模型路由/预算控制）→ 平台化部署与监控。这正是"AI 推理平台"的标准架构。
2. **Lab 03/04/05 构成"数据 + LLM"故事线**：RAG 是数据工程（分块、清洗、索引、质量），评估是数据质量体系，Text2SQL 串起数据库知识。**有数据工程背景的学习者在这里有天然优势。**
3. **Lab 07/08 补足推理与训练层**：推理引擎的核心是 vLLM 的 PagedAttention/连续批处理、KV Cache、GPU 显存估算 —— Lab 08 把这些原理和你已验证的 K8s GPU 调度知识串起来。

## 五、面向求职者的配套手册

准备面试可配合隔壁的 [interview-prep](../interview-prep/)：其中 06-LLMOps 篇与本仓库逐实验挂钩，02-数仓建模、03-大数据引擎、04-湖仓与实时数仓、05-场景设计题覆盖数据方向全部高频考点。

## 延伸学习资源（做完实验后按需深入）

- vLLM 官方文档的 PagedAttention 论文解读（Lab 08 的延伸）
- LangChain/LlamaIndex 二选一深入（Lab 03 的延伸）
- 《Designing Machine Learning Systems》(Chip Huyen) —— 平台视角的最佳教材
- K8s Gateway API Inference Extension、Kueue、DRA（Dynamic Resource Allocation）—— AI Infra 的 K8s 演进方向，值得关注

## 六、验证状态总表（透明说明）

| 实验 | 验证结果 | 说明 |
|---|---|---|
| Lab 01 | ✅ 完整验证 | qwen2.5:0.5b-instruct（397MB）本机 Metal 推理，OpenAI 兼容 API 实测 |
| Lab 02 | ✅ 完整验证 | LiteLLM 网关实测：路由/虚拟 key/预算/日志 |
| Lab 03 | ✅ 完整验证 | 中文嵌入（bge-m3）+ Chroma + 检索问答，知识库为可替换的 Markdown 文件 |
| Lab 04 | ✅ 完整验证 | 评估集 + 检索命中率/忠实度指标实测 |
| Lab 05 | ✅ 完整验证 | 对本实验自带的样例 MySQL 数据库 Text2SQL，含只读护栏与中文乱码修复实录 |
| Lab 06 | ✅ 完整验证 | RAG 服务容器化部署进 kind，Ingress 暴露，Prometheus 抓取指标 |
| Lab 07 | ⚙️ 部分验证 | venv/依赖安装已验证；训练环节给出两条路径（本机 MLX / 云端 Colab），训练时长本机未完整执行，命令可直接复制 |
| Lab 08 | 📖 原理篇 | 本机无 GPU，无法实操；文档覆盖 vLLM 原理、显存估算、GPU 调度，全部标注"原理" |

## 相关模块

完成本模块后，可以继续学习：

- **[agent-labs](../agent-labs/)** - Agent 开发（基于本模块的网关和 RAG 能力构建智能体）
- **[k8s-labs](../k8s-labs/)** - K8s 基础（Lab 06 部署依赖 K8s 知识，建议先完成 K8s Lab 01-07）
- **[interview-prep](../interview-prep/)** - 面试准备（06-LLMOps 篇与本模块逐实验挂钩）
- **[algo-labs](../algo-labs/)** - 算法面试（10 专题覆盖手撕代码能力）
- **[career-portfolio](../career-portfolio/)** - 职业发展（将本模块实验转化为简历素材）
