# Lab 07 — LoRA 微调入门：模型层的第一课

> ⚙️ 验证状态：依赖安装与数据格式验证 ✅；完整训练本机未跑完（见"验证说明"），命令已按本机环境写好可直接执行。

## 📖 本章学习指导

> 建议时长 **3 小时（本机冒烟）+ Colab 训练另计** ｜ 前置：Lab 01/04 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q7

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3（"为什么不用微调"比"怎么微调"更重要）
2. **跑**（40min）：本机验证到 MLX 环境可用 + 数据格式构造 + `--iters 20` 冒烟（完整训练去 Colab）
3. **验收自测**：① LoRA 原理一句话？② 什么时候该微调什么时候不该？③ 训练数据三原则？④ 留出集的作用？
4. **产出**：一份你自己的训练数据样例（从 Lab 04 评估的坏案例转化）

## 学习目标

- 搞懂 **LoRA/QLoRA** 为什么让"人人可微调"成为可能
- 掌握微调的工程流程：**数据格式 → 训练 → 评估 → 部署**（和 Lab 01~06 的链路接上）
- 知道什么时候该微调、什么时候不该（比怎么训更重要）

## 核心问答

**Q1：LoRA 的原理？为什么不全参数微调？**

> 参考答法：冻结原模型权重，只在旁边加两个低秩矩阵（A: d×r，B: r×d，r 通常 8~64），训练时只更新这两个小矩阵。参数量降到 1% 以下（7B 模型全参要 ~56GB 显存，LoRA r=8 只要几 GB），QLoRA 再把基座量化到 4bit 进一步压缩。产物是一个几十 MB 的 adapter，可以叠在任意基座上、可插拔 —— 这就是"一个基座 + 多个任务 adapter"的平台化思路，对 AI Infra 来说是**模型资产的多租户管理问题**。

**Q2：什么场景该微调，什么场景不该？**

> 参考答法：微调改变的是**行为/风格/格式**（输出格式、领域话术、指令遵循），**不擅长注入知识**（知识用 RAG，可更新可溯源）。经验序：先 prompt 工程（Lab 05 实测一行 few-shot 就解决了问题），再 RAG（Lab 03/04），两者都到顶了、且任务模式固定（如固定格式的抽取），才微调。理解"为什么不用微调"往往比会微调更重要。

**Q3：微调数据怎么准备？**

> 参考答法：质量 > 数量，几百到几千条高质量样本即可起效。格式是 messages 对（instruction/input/output），**输出必须是你真正想要的样子**（把 Lab 04 评估里发现的所有坏案例收集起来就是最好的训练集 —— 评估数据直接变训练数据，闭环）。注意数据泄漏与去重、以及用留出集防过拟合。

## 动手实验

### 路线 A：本机 Apple Silicon（MLX，可验证安装）

```bash
# 环境准备（本机已验证到这一步）
.venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ mlx mlx-lm
export HF_ENDPOINT=https://hf-mirror.com        # 国内拉 HF 模型必须走镜像（实测要点）

# 数据：把 Lab 04 评估发现的坏案例做成训练对（示例结构）
# train.jsonl 每行: {"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}

# 训练（0.5B 模型 + LoRA，本机 16GB 可跑，预估 1~2 小时）：
.venv/bin/python -m mlx_lm lora \
  --train ./data/train.jsonl \
  --model mlx-community/Qwen2.5-0.5B-Instruct \
  --iters 200 --batch-size 2 --learning-rate 1e-5

# 训练完：把 adapter 叠加导出成 GGUF → ollama 导入（接回 Lab 01 的推理链路）
.venv/bin/python -m mlx_lm generate --model mlx-community/Qwen2.5-0.5B-Instruct \
  --adapter-path adapters --prompt "容器被OOM杀掉的退出码是多少"
```

### 路线 B：云端免费算力（Colab T4，推荐第一次完整跑通）

打开 Google Colab（T4 GPU），按同样命令跑 `unsloth` 的 QLoRA notebook（unsloth 在免费 T4 上微调 3B~7B 模型 1 小时内可完成）。本机没有 GPU、Linux 依赖（bitsandbytes）在 macOS 不可用，所以完整训练环节**本机无法验证**，这是本实验唯一标记为"本机未执行"的部分 —— 教程与命令均为通用可复制版本。

### 3. 微调后的回归（最重要的一步，接 Lab 04）

```bash
# 把 Lab 04 的评估集对微调后模型再跑一遍：
# 指标对比：忠实度、拒答正确率有没有提升？有没有把原来对的题改错（灾难性遗忘的信号）？
```

## 观察与思考

1. adapter 几十 MB、基座 1GB：多任务场景怎么组织？（一个基座 + N 个 adapter 目录，推理网关按请求选 adapter —— vLLM 原生支持 LoRA adapter 热加载，Lab 08 的伏笔）
2. 训练数据里混入了错误答案会怎样？（模型忠实学错 —— 微调的"数据质量决定论"，和数仓的"垃圾进垃圾出"同源）
3. 为什么要留出集？（没有留出集，训练损失下降 ≠ 真的变好 —— 和 Lab 04 的评估纪律完全一致）

## 验证说明（透明）

本机（16GB Apple Silicon）已验证：mlx/mlx-lm 安装、数据格式构造、HF 镜像下载路径。**未验证**：完整训练迭代（时长与显存行为需在 GPU 环境或长时本机任务中观察）。若在本机跑，建议先用 `--iters 20` 冒烟验证流程，再拉满迭代数。
