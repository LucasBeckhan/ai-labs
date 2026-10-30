# Lab 02 — LiteLLM 网关：统一接入、虚拟 key、限流与用量观测

> ✅ 已在本机完整验证：别名路由、鉴权（401/400/200）、虚拟 key、RPM 限流（429）、key 用量统计。
> 架构位：`应用 → LiteLLM 网关(:4000) → 宿主机 Ollama(:11434)`

## 📖 本章学习指导

> 建议时长 **3 小时** ｜ 前置：Lab 01 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q8-Q9

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3
2. **跑**（60min）：Postgres + 网关启动 → 鉴权三连 → **虚拟 key 限流（第 4 发 429 是本章高光）** → key 台账
3. **破坏练习**（30min）：① 错 key 看状态码；② rpm_limit 调 1 体验严格限流；③ 删 Postgres 再建 key，看 "DB not connected"——理解 key 存在哪
4. **验收自测**：① 网关四职责？② 为什么虚拟 key 必须落库？③ 限流 vs 预算？④ 网关为什么能水平扩展？
5. **产出**：你自己签发的一个虚拟 key（记录 alias 与限额）

## 学习目标

- 理解"AI 网关"在生产里的四个职责：**统一协议、模型路由、配额限流、用量观测**
- 会部署 LiteLLM Proxy，配置模型别名（应用与后端模型解耦）
- 掌握虚拟 key 体系：按团队/项目发 key、限 RPM、查花费

## 核心问答

**Q1：为什么需要一个 AI 网关？直连模型 API 不行吗？**

> 参考答法：直连时每条业务线各自管 key、各自处理限流重试、成本无法归因。网关统一收口后：① 应用只认**模型别名**，后端模型随时替换/灰度（本实验用同一模型起了 `qwen-small`/`qwen-creative` 两个别名）；② 虚拟 key 按**团队/项目**发放，天然带鉴权、限流、预算；③ 所有调用过网关，**token 用量和花费可归因到人**。一句话：把模型当"需要治理的资源"管理，就像数据库中间件之于数据库。

**Q2：限流怎么做？RPM/TPM 和预算什么区别？**

> 参考答法：RPM/TPM 限**速率**（保护后端、防突发），预算（max_budget）限**累计花费**（控成本，按 key/团队/周期）。本实验实测：`rpm_limit=3` 的虚拟 key，第 4 发即 429。生产上通常速率+预算双层：RPM 兜底防打挂，月度预算控总成本，超限自动降级到便宜模型或拒绝。

**Q3：网关怎么保证"应用无感切换后端"？**

> 参考答法：应用只写 `model: qwen-small`；配置里 `qwen-small` 今天指向本地 Ollama，明天指向 vLLM 集群或商用 API，只改网关配置。配合 `drop_params: true`，应用带了后端不支持的参数也不报错。**这就是 Lab 06 能把网关原样搬进 K8s 的原因：架构不变，只改 api_base。**

## 动手实验

### 0. 依赖（一次性）

```bash
cd llmops-labs
.venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ "litellm[proxy]" prisma
# LiteLLM 的 key 管理依赖 prisma 客户端，装完要生成一次（清华 pypi 对部分 wheel 403，用阿里云源）
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m prisma generate \
  --schema="$PWD/.venv/lib/python3.11/site-packages/litellm/proxy/schema.prisma"
```

### 1. 启动 Postgres（虚拟 key 必须落库）

```bash
docker run -d --name litellm-postgres \
  -e POSTGRES_PASSWORD=lab2pass -e POSTGRES_USER=litellm -e POSTGRES_DB=litellm \
  -p 5433:5432 postgres:16-alpine
```

> 实测教训：不配 `DATABASE_URL` 时 master_key 鉴权可用，但**创建虚拟 key 会直接报 "DB not connected"** —— key 管理一定要数据库，这就是生产的真实形态。

### 2. 启动网关

```bash
cd lab02-litellm-gateway
# 启动命令前面的两个变量是传给网关进程的环境变量，作用分别是：
LITELLM_LOCAL_MODEL_COST_MAP=True \
DATABASE_URL="postgresql://litellm:lab2pass@localhost:5433/litellm" \
../.venv/bin/litellm --config config/litellm-config.yaml --port 4000 &
```

两个环境变量的作用（面试能讲出来就是"懂配置管理"）：
- `LITELLM_LOCAL_MODEL_COST_MAP=True`：离线环境跳过 GitHub 拉取模型价格表，用内置备份
  （不设的话启动会反复重试拉取，慢几十秒）
- `DATABASE_URL`：虚拟 key 的存储数据库连接串——key 管理必须有 DB，网关本身无状态

```bash
curl -s http://localhost:4000/health/liveliness   # 就绪约 20s
```

### 3. 鉴权三连（实测结果）

```bash
# 无 key      → 401（网关拒绝匿名访问）
# 错 key      → 400（Invalid Proxy Server Token）
# master key  → 200，回答 "4"，响应 model 字段是别名 qwen-creative
curl -s -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-labs-master" -H "Content-Type: application/json" \
  -d '{"model":"qwen-creative","messages":[{"role":"user","content":"只回答数字：2+2=?"}]}'
```

注意响应里的 `usage: {prompt_tokens, completion_tokens}` —— **成本观测的原始数据从这里来**。

### 4. 虚拟 key + 限流（本实验高潮，实测复现）

```bash
# 发一个限 3 RPM、只允许 qwen-small 的 key
KEY=$(curl -s -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer sk-labs-master" -H "Content-Type: application/json" \
  -d '{"key_alias":"lab2-demo","rpm_limit":3,"models":["qwen-small"]}' | python3 -c "import json,sys; print(json.load(sys.stdin)['key'])")

# 连打 5 发（实测）：
# 第1发: 200   第2发: 200   第3发: 200   第4发: 429   第5发: 429
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "第${i}发: %{http_code}\n" -X POST http://localhost:4000/v1/chat/completions \
    -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
    -d '{"model":"qwen-small","messages":[{"role":"user","content":"hi"}]}'
done

# 查 key 的台账（实测输出）：
# 别名: lab2-demo | rpm限制: 3 | 允许模型: ['qwen-small'] | spend(USD): 0.0
```

> 429 就是生产的"限流生效"信号。本地 Ollama 免费所以 spend 恒为 0；换成计费后端后，spend 按模型价格表自动累计 —— 预算告警、按团队分摊都有了。

### 5. 观察网关日志

网关终端里每条请求都记录：模型别名、后端、tokens、耗时。这就是**观测层的最小形态**；Lab 06 会把 Prometheus 指标接上。

## 观察与思考

1. 如果要把 `qwen-small` 切到更强的 `qwen2.5:1.5b`，改哪里？（只改 config 里该别名的 litellm_params.model，应用零改动 —— 重启网关即可）
2. 多个团队共用网关，怎么防止互相影响？（每个团队独立虚拟 key + 独立 rpm/预算；网关层还能做并发队列和降级路由）
3. 网关本身是单点吗？（是，所以 Lab 06 会把它部署成 K8s Deployment 多副本 —— 网关无状态、key 在 Postgres，天然可水平扩展）

## 常见坑

- 忘了 `LITELLM_LOCAL_MODEL_COST_MAP=True` 时，启动会反复重试拉 GitHub 的价格表然后超时回退（能起但慢几十秒）
- `prisma generate` 必须用 litellm 包内的 schema.prisma 执行一次，否则任何带鉴权的请求 500（`No module named 'prisma'`，实测踩过）
- Postgres 容器删除后虚拟 key 全部消失 —— key 的持久化在 DB 不在网关，这是理解网关无状态的关键
