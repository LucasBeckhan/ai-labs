# Lab 05 — Text2SQL Agent：让大模型查数据库（带生产级护栏）

> ✅ 已在本机完整验证，目标库是本实验自带的样例电商数据库（`setup/sample-db.sql` 一键初始化）。本实验完整记录了一次"优化阶梯"：重试 → 升级模型 → few-shot，最后一级零成本解决 —— 这个过程值得完整体验一遍。

## 📖 本章学习指导

> 建议时长 **3 小时** ｜ 前置：Lab 02 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q7/Q10

**学习循环：**
1. **读**（20min）：核心问答 Q1-Q3
2. **跑**（60min）：起样例库 → 三连测试（**DELETE 被护栏拦截是本章高光**）→ 完整复现优化阶梯
3. **破坏练习**（30min）：① 删掉 few-shot 行，亲眼看模型漏 FROM 报 1054，走一遍重试与升级；② 把护栏的白名单改成黑名单式判断，找一个能绕过的写法（体会白名单思想）
4. **验收自测**：① 安全三件套为何缺一不可？② 重试的天花板？③ 优化为什么按 prompt→模型 排序？④ Agent 的本质？
5. **产出**：把你自己的数据库（或加表加数据）接进来跑通一次

## 学习目标

- 实现 Text2SQL 最小闭环：**schema 注入 → SQL 生成 → 护栏校验 → 只读执行 → 错误回传重试 → 模型升级**
- 掌握 LLM 应用安全三件套：**只读账号、SQL 白名单、强制 LIMIT**
- 建立"优化按成本排序"的工程直觉：prompt 优化 < 模型升级

## 核心问答

**Q1：Text2SQL 怎么保证安全？**

> 参考答法：三层防线，**权限层最可靠**。① 数据库层：给 LLM 专用只读账号（GRANT SELECT），就算模型越狱生成 DELETE 也执行不了；② 应用层：SQL 白名单校验（只放行 SELECT，拦截写关键字和 load_file 等），无 LIMIT 的查询强制加 LIMIT，执行设超时；③ prompt 层：明确"只能写 SELECT"。**prompt 层是提示，不是防线** —— 本实验实测：模型对"删除所有用户"真的生成了 `DELETE FROM users;`，靠护栏拦下的（这正是护栏存在的意义）。

**Q2：模型生成的 SQL 执行报错怎么办？**

> 参考答法：把数据库报错回传给模型重试（agent 的最小闭环）。但要认识到**重试有天花板**：本实验 0.5B 模型对同一个错误（漏写 FROM）重试两次都犯同样的错，升级到 1.5B 也没修好，最后在 prompt 里加**一条 few-shot 示例**（问题→SQL 范例）后一次成功 —— 优化顺序按成本排：先 prompt 工程（零成本），再升级模型（推理成本翻倍），最后才考虑微调。

**Q3：这算"Agent"吗？**

> 参考答法：是工具调用（function calling）的最小形态 —— 模型在循环里"调用工具"（执行 SQL）、观察结果、决定下一步。生产 Agent 是这个骨架的扩展：更多工具（查库、调 API、检索）、规划步骤、多轮反思。理解了这个最小闭环，框架（LangChain 等）只是把这个循环工程化。

## 动手实验

### 0. 启动样例数据库（一键）

```bash
# 样例库 = 迷你电商（users/products/orders 三张表 + 只读账号 llm_ro），SQL 已在 setup/sample-db.sql
docker run -d --name llmops-mysql \
  -e MYSQL_ROOT_PASSWORD=root_lab_only -p 3308:3306 \
  -v "$PWD/setup/sample-db.sql":/docker-entrypoint-initdb.d/init.sql:ro \
  mysql:8.0 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
sleep 30   # 等初始化完成
docker exec llmops-mysql mysql -ullm_ro -pllm_ro_pass -e "SELECT COUNT(*) FROM shop.users"
# 实测：6
```

> 两个实测踩过的坑写进 SQL 和命令里了：① 初始化脚本默认可能以 latin1 客户端字符集执行，**中文会存成乱码**（SQL 里的 `SET NAMES utf8mb4` 就是为此）；② `--character-set-server` 是 mysqld 参数，必须写在镜像名之后。
> 已有自己的 MySQL？把连接信息用环境变量传给脚本即可（`DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`），脚本会自动建只读账号需要 root 权限，参考 SQL 文件最后一行。

### 1. 跑通（先确认 Lab 02 网关运行中）

```bash
cd lab05-text2sql-agent
LITELLM_LOCAL_MODEL_COST_MAP=True ../.venv/bin/python text2sql.py
```

实测输出（三连）：

```
Q: 查一下有多少个用户？
LLM 生成 SQL: SELECT COUNT(DISTINCT user_id) AS num_users FROM users;
结果 1 行: ['num_users']  (6,)

Q: 每个城市分别有多少个用户？
LLM 生成 SQL: SELECT city, COUNT(user_id) AS user_count FROM users GROUP BY city;
结果 4 行: ['city', 'user_count']  ('上海', 2) ('北京', 2) ('广州', 1) ('深圳', 1)

Q: 删除所有用户
LLM 生成 SQL: DELETE FROM users;
🛑 护栏拦截：只允许 SELECT 查询
```

### 2. 完整复现"优化阶梯"（15 分钟）

把 `generate_sql` 的 prompt 里那一行 few-shot 示例删掉，依次体验：

1. **原始 prompt**：`查一下有多少个用户？` → 模型生成 `SELECT COUNT(account_id) AS user_count;`（漏了 FROM）→ 报错 1054
2. **重试**：错误回传 2 次 → 模型重复同一个错（0.5B 的能力地板）
3. **升级模型**：网关别名 `qwen-strong`（1.5B，Lab 02 配置里已加）→ **仍修不好** —— 升级不是万能的
4. **few-shot**：加一行示例 → 一次成功

> **结论**："我们习惯性地觉得模型不行就换模型，但实测同一问题 few-shot 一行字解决了，成本是零。LLM 应用的优化要按边际成本排：prompt → RAG/工具 → 模型 → 微调。"

## 观察与思考

1. schema 注入是 Text2SQL 的命门：表一多（几百张）prompt 就爆了 —— 生产方案是 schema linking（先检索相关表再注入），和 RAG 思想同源。
2. 把样例库换成你公司的库要注意什么？（敏感字段脱敏、行列级权限、慢查询超时 —— 脚本的 read_timeout=5 就是第一道闸）
3. 换成"生成 SQL + 展示给用户确认再执行"的交互会怎样？（Human-in-the-loop：写操作永远该走这条路径，本实验是纯读场景所以护栏+只读账号就够了）

## 常见坑

- 模型偶尔输出 markdown 代码块（\`\`\`sql），要剥壳后再校验（脚本已处理）
- `temperature=0` 不是绝对确定，同一问题两次可能生成略有差异的 SQL —— 对 SQL 任务再叠加护栏兜底
- 错误回传重试时，错误消息要截断（本实验截到 80 字符），否则把几百行堆栈塞进 prompt 又贵又乱
- **中文数据必须两端都设 utf8mb4**：容器初始化 SQL 加 `SET NAMES utf8mb4`，pymysql 连接加 `charset="utf8mb4"`（实测漏任何一头都是乱码）
- 账号密码别提交到 git（本实验为演示写死在脚本里，生产走环境变量/密钥管理）
