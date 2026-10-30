# Lab 01 — 本地跑通开源模型 + OpenAI 兼容 API

> ✅ 本实验已在本机（Apple Silicon 16GB）完整验证：qwen2.5:0.5b-instruct（397MB），Metal 加速推理。

## 📖 本章学习指导

> 建议时长 **2 小时** ｜ 前置：无（独立章节）｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q1

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3
2. **跑**（40min）：curl 调用 → temperature 对照（0 和 1.5 各两次）→ **观察 usage 的 token 计数**
3. **破坏练习**（15min）：① 模型名写成 qwen2.5（不带 tag）看 404；② max_tokens 不设时多问几次长问题，体会失控风险
4. **验收自测**：① 量化是什么？② 为什么大家兼容 OpenAI 格式？③ temperature 怎么选？④ token 为什么是计量单位？
5. **产出**：一条能跑通的 curl 命令模板（存进笔记）

## 学习目标

- 建立 LLM 的关键"体感单位"：**参数量、量化、token、上下文窗口**
- 会用 Ollama 在本地跑开源模型，理解它的 **OpenAI 兼容 API** 为什么是行业事实标准
- 学会控制推理参数（temperature/top_p/max_tokens），知道它们对输出的影响

## 核心问答

**Q1：什么是量化（quantization）？为什么本地能跑 0.5B 模型？**

> 参考答法：把模型权重从 FP16（2 字节/参数）压缩到更低精度（如 Q4，约 0.5 字节/参数），体积和显存占用近似线性缩小、精度损失很小。Ollama 默认用 GGUF Q4 量化 —— 0.5B 模型 FP16 要 ~1GB，Q4 后 397MB，8GB 内存的笔记本就能跑。推理侧的对应概念：**KV Cache**（按 token 数增长显存）、**PagedAttention**（vLLM 对 KV Cache 的分页管理，Lab 08 深入）。

**Q2：为什么大家都兼容 OpenAI API 格式？**

> 参考答法：OpenAI 的 chat/completions 接口（messages 数组 + choices 响应）成了行业事实标准 —— Ollama、vLLM、LiteLLM、各大模型厂商都兼容它。好处是**应用层可以无感切换后端**：开发用本地 Ollama，生产换 vLLM 集群或商用 API，代码只改 base_url。这也是 Lab 02 网关存在的前提。

**Q3：temperature 和 top_p 是干什么的？**

> 参考答法：都是控制采样随机性。temperature 缩放 logits 分布（0=贪心，越大越发散）；top_p 截断累积概率（只在概率和超过 p 的候选里采样）。工程要点：**SQL 生成、抽取类任务用低 temperature（0~0.2）求稳；创意生成用高值求活**。Lab 05 的 Text2SQL 会实际用到这一点。

## 动手实验

### 1. 安装并启动（已完成的可跳过）

```bash
brew install ollama
ollama serve &                      # 前台跑也行；brew services start ollama 可注册常驻
curl -s http://localhost:11434/api/version   # {"version":"0.40.10"} 即服务正常
```

### 2. 拉模型，看体积

```bash
ollama pull qwen2.5:0.5b-instruct   # 397MB，Q4 量化的 0.5B 中文模型
ollama list
```

> 想要更高质量可换 `qwen2.5:1.5b`（约 1GB）—— 你的 16GB 内存跑 3B 以下都轻松，这就是"体感参数量"。

### 3. 用 OpenAI 兼容 API 调用（本实验核心）

```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:0.5b-instruct","messages":[{"role":"user","content":"用一句话说明什么是Kubernetes"}]}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

实测输出：`Kubernetes是一种开源的容器化平台，能帮助用户更容易地创建、管理、扩展和管理应用……`

**注意两点**：① 这就是标准 OpenAI 格式 —— 换成任何兼容后端只需改 base_url；② 响应里的 `usage` 字段有 prompt_tokens/completion_tokens，**token 是 LLMOps 成本和限流的计量单位**（Lab 02 会用它做预算控制）。

### 4. 感受推理参数

```bash
# temperature=0：两次提问同一问题，回答应基本一致
curl -s http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:0.5b-instruct","temperature":0,"messages":[{"role":"user","content":"给我一个Python函数名，只回答名字"}]}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
# 连跑两次对比，再换 temperature=1.5 对比发散程度
```

### 5. 观察 token 计数

```bash
curl -s http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:0.5b-instruct","messages":[{"role":"user","content":"1+1等于几"}]}' \
  | python3 -c "import json,sys; u=json.load(sys.stdin)['usage']; print(u)"
```

观察 prompt_tokens 与 completion_tokens —— **Lab 06 会把这个指标接进 Prometheus 做成本监控**。

## 观察与思考

1. 0.5B 和 70B 模型的差距体现在哪？（知识广度、复杂推理、指令遵循；0.5B 适合分类/抽取/路由，复杂任务要更大模型 —— 这就是 Lab 02 模型路由的存在理由）
2. 上下文窗口是什么？（模型一次能"看到"的最大 token 数；RAG 的意义之一就是把"塞不下"的知识检索出最相关的几段塞进去 —— Lab 03 实操）
3. 为什么推理服务要"批处理"？请求少时 GPU 在干嘛？（Lab 08 详解：连续批处理让新请求插队进正在解码的批次，是 vLLM 高吞吐的核心）

## 常见坑

- `ollama serve` 默认只监听 127.0.0.1 —— 本机实验够用；要让 Docker/K8s 里的服务访问宿主机模型，需要 `OLLAMA_HOST=0.0.0.0 ollama serve`（Lab 06 会用到）
- 模型名要带完整 tag（`qwen2.5:0.5b-instruct` 而不是 `qwen2.5`），否则 404
- macOS 首次推理有几秒模型加载延迟，之后是热缓存
