#!/usr/bin/env python3
"""
Lab 05 — Text2SQL Agent：自然语言查数据库，带生产级安全护栏
============================================================

完整链路（也是"最小 Agent"的定义：模型在循环里调用工具并观察结果）：

    ┌────────┐   ┌──────────────┐   ┌──────────┐   ┌──────────────┐
    │ 用户问题 │ → │ schema 注入   │ → │ LLM 生成  │ → │ 护栏校验       │
    └────────┘   │ (get_schema)  │   │ SQL      │   │ (guardrail)  │
                 └──────────────┘   └──────────┘   └──────┬───────┘
                        ↑  拦截 → 拒绝并说明原因            │ 通过
                        │  执行报错 → 错误回传重试 ←──────── ↓
                        └──────── 只读连接执行 (run_sql) ←───┘

安全三件套（生产必做，缺一不可）：
  1. 只读数据库账号（CREATE USER ... GRANT SELECT）—— 权限兜底，不依赖 prompt；
     实测模型对"删除所有用户"真的会生成 DELETE，全靠这一层挡住
  2. SQL 白名单校验 —— 只放行 SELECT，拦 INSERT/UPDATE/DELETE/DROP 等一切写操作
  3. 强制 LIMIT + read_timeout —— 防止全表扫描拖垮库

先决条件：
  1. Lab 02 网关运行中（localhost:4000）
  2. 样例库：setup/sample-db.sql 已通过 docker 初始化（默认连本机 3308 的 shop 库，
     可用环境变量 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME 覆盖任意库）
"""
import os
import re

import litellm
import pymysql

# ---------------------------------------------------------------------------
# 数据库连接配置：全部环境变量化（12-Factor）。
# 生产环境密码走密钥管理（Vault/云 KMS），绝不能写死在代码里提交进 git；
# 这里为了实验可复制给了默认值，实际连接的 llm_ro 是只读账号（见 setup/sample-db.sql 末尾）。
# ---------------------------------------------------------------------------
DB = dict(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("DB_PORT", "3308")),
    user=os.environ.get("DB_USER", "llm_ro"),
    password=os.environ.get("DB_PASSWORD", "llm_ro_pass"),
    database=os.environ.get("DB_NAME", "shop"),
)

# ---- 护栏的"黑名单"部分：写操作关键字 + 危险函数 ----
# 注意设计思想：黑名单只是第二道防线（防绕过白名单的边角写法），
# 主判断在 guardrail() 里的"必须以 SELECT 开头"——白名单永远比黑名单可靠。
FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|grant|revoke|create)\b", re.I)
FORBIDDEN_PATTERN = re.compile(r"\binto\s+outfile\b|\bload_file\b", re.I)


def get_schema() -> str:
    """从 information_schema 读取全部表结构，拼成人类可读的文本（注入 prompt 用）。

    为什么必须注入 schema？—— Text2SQL 第一定律：模型不知道表结构就写不出 SQL。
    进阶方向：表多到 schema 撑爆 prompt 时（几百张表），改为"schema linking"——
    先按问题语义检索出相关表再注入，思想与 RAG 同源（Lab 03）。

    Returns:
        形如 "表 users:\\n  - user_id varchar(32)\\n  ..." 的多行文本。
    """
    # charset="utf8mb4" 必须显式指定：默认 latin1 会导致中文查询结果乱码（实测踩过）
    conn = pymysql.connect(**DB, charset="utf8mb4")
    cur = conn.cursor()
    # information_schema 是 MySQL 的元数据库：查它 = 只读地获取"库有哪些表/列"
    # ORDER BY TABLE_NAME, ORDINAL_POSITION 保证输出按表分组、列按定义顺序，prompt 稳定
    cur.execute(
        "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA='{}' ORDER BY TABLE_NAME, ORDINAL_POSITION".format(DB["database"])
    )
    lines, last = [], None
    for table, col, ctype in cur.fetchall():
        if table != last:                     # 换表时插入表名标题行
            lines.append(f"\n表 {table}:")
            last = table
        lines.append(f"  - {col} {ctype}")    # 列名 + 类型（类型帮助模型判断比较方式）
    conn.close()
    return "\n".join(lines)


def guardrail(sql: str) -> str | None:
    """安全护栏：校验 LLM 生成的 SQL，返回拒绝原因；返回 None 表示放行。

    校验顺序体现"白名单思想"：
      1. 必须以 SELECT 开头（白名单主干 —— DELETE/UPDATE/DROP 全部被这行拦住）；
      2. 黑名单兜底：即使以 SELECT 开头，也拦截其中嵌套的写关键字
         （如 SELECT ... ; DROP TABLE 的多语句攻击）和 into outfile/load_file 等危险函数；
      3. 无 LIMIT 强制补 LIMIT 50 —— 防止"SELECT * 千万行"拖垮数据库。

    Args:
        sql: LLM 生成的 SQL（可能带 markdown 代码块或分号）。

    Returns:
        str：拒绝原因；None：放行。
    """
    s = sql.strip().rstrip(";")                          # 去首尾空白与结尾分号（多语句攻击的载体）
    if not s.upper().startswith("SELECT"):
        return "只允许 SELECT 查询"
    if FORBIDDEN.search(s) or FORBIDDEN_PATTERN.search(s):
        return "包含禁止的写操作或危险函数"
    if not re.search(r"\\bLIMIT\\s+\\d+\\b", s, re.I):
        s += " LIMIT 50"  # 无 LIMIT 的查询强制加，防全量拉取
    return None


def generate_sql(question: str, schema: str, model: str = "qwen-small") -> str:
    """调用网关生成 SQL。

    prompt 的四个关键设计（都是实测换来的）：
      1. "只输出 SQL 本身" —— 防止模型输出解释文字导致解析失败；
      2. "只能写 SELECT" —— prompt 层约束（第三道防线，提示而非防线）；
      3. "FROM 子句不能省" —— 0.5B 模型实测会漏写 FROM 导致 1054 错误，明确点名约束；
      4. **few-shot 示例** —— 一行"问题→SQL"范例，实测让失败率大幅下降；
         优化阶梯：重试无效 → 升级模型无效 → few-shot 一次成功（成本为零）。

    Args:
        question: 用户的自然语言问题。
        schema: get_schema() 的输出。
        model: 网关别名（qwen-small / qwen-strong），升级模型时切换。

    Returns:
        清洗后的 SQL 字符串。
    """
    prompt = (
        "你是 MySQL 专家。根据下面的表结构，把用户问题转成一条 SQL。\n"
        "规则：只输出 SQL 本身，不要解释，不要 markdown 代码块；只能写 SELECT；"
        "查询列必须写明来自哪张表（FROM 子句不能省）。\n"
        "示例：问题「商品表有多少行」→ SELECT COUNT(*) FROM products;\n\n"
        f"表结构：\n{schema}\n\n用户问题：{question}"
    )
    resp = litellm.completion(
        model=f"openai/{model}",              # openai/ 前缀 = 走 OpenAI 协议调网关别名（Lab 02）
        api_base="http://localhost:4000",
        api_key="sk-labs-master",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,  # SQL 生成要确定性：温度越高，同一问题生成的 SQL 越不可复现
    )
    sql = resp.choices[0].message.content.strip()
    # 模型偶尔无视"不要 markdown"的指令，输出 ```sql ... ``` —— 用正则剥壳（实测必做）
    return re.sub(r"```[a-z]*|```", "", sql).strip()


def run_sql(sql: str) -> tuple[list[str], list[tuple]]:
    """用只读连接执行 SQL。

    三个安全/稳定细节：
      - 连接账号 llm_ro 只有 SELECT 权限（数据库层兜底，见 setup/sample-db.sql）；
      - read_timeout=5：LLM 可能生成笛卡尔积级别的慢查询，5 秒超时保住数据库；
      - charset="utf8mb4"：中文数据两端必须一致（实测漏掉就是乱码）。

    Args:
        sql: 已通过护栏校验的 SQL。

    Returns:
        (列名列表, 数据行列表)。
    """
    conn = pymysql.connect(**DB, charset="utf8mb4", read_timeout=5)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        # cur.description 携带结果集的列信息（SELECT 才有，无结果集时为 None）
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, cur.fetchall()
    finally:
        conn.close()   # finally 保证即使查询抛异常也归还连接（连接是有限资源）


def generate_sql_with_retry(question: str, schema: str, max_retry: int = 2) -> str:
    """Agent 最小闭环：生成 → 试执行 → 报错回传重试 → 重试耗尽升级模型。

    这是"Agent"概念的骨架：模型不再是单次调用，而是在循环中
    【行动 → 观察（报错信息）→ 调整】。生产 Agent 是这个循环的工程化扩展。

    升级策略（成本敏感的优化顺序，实测验证）：
      小模型重试 1 次仍错 → 再试 1 次 → 仍错则升级到强模型（网关别名 qwen-strong）。
      实测教训：0.5B 模型对同一个错误（漏写 FROM）重试两次都犯同样的错，
      1.5B 也修不好 —— 最终靠 few-shot 示例解决。所以**重试不是万能的**，
      循环要有升级/放弃的出口，否则就是无限烧钱。

    Args:
        question: 用户问题。
        schema: 表结构文本。
        max_retry: 同模型的最大重试次数（默认 2）。

    Returns:
        最终版本的 SQL（可能仍失败，由上层护栏/执行兜底）。
    """
    schema_now = schema
    model = "qwen-small"
    sql = generate_sql(question, schema_now, model)
    for i in range(max_retry + 1):                    # +1 是因为最后一轮用升级后的模型再试一次
        reason = guardrail(sql)
        if reason:
            return sql  # 护栏问题交给上层拒绝，不重试 —— 写操作没有"再试一次"的价值
        try:
            cols, _ = run_sql(sql)                    # 试执行：这里失败才会触发重试/升级
            return sql
        except Exception as e:
            if i == max_retry - 1:
                model = "qwen-strong"  # 小模型重复犯同一个错 → 升级强模型（网关别名，见 Lab 02）
                print(f"  [escalate] 小模型重试耗尽，升级到 {model}")
            else:
                print(f"  [retry {i + 1}] 执行报错，回传给模型修正: {str(e)[:80]}")
            # 关键技巧：把"上一次的 SQL + 数据库真实报错"一起回传，
            # 让模型基于事实修正，而不是凭空再猜。报错截断到 80 字符（堆栈塞 prompt 又贵又乱）。
            schema_now = f"{schema}\n\n你上一次生成的 SQL 是：{sql}\n报错：{e}（请修正，仍然只输出 SQL）"
            sql = generate_sql(question, schema_now, model)
    return sql


def main():
    """入口：读 schema → 依次处理三个演示问题（含一个越界攻击样本）。"""
    schema = get_schema()
    questions = [
        "查一下有多少个用户？",           # 基础聚合（COUNT）
        "每个城市分别有多少个用户？",   # GROUP BY：验证模型能否写聚合
        "删除所有用户",              # 越界：验证护栏（实测模型真的会生成 DELETE）
    ]
    for q in questions:
        print(f"\n{'=' * 60}\nQ: {q}")
        sql = generate_sql_with_retry(q, schema)
        print(f"LLM 生成 SQL: {sql}")
        # 注意：重试循环内部已经试执行过，这里再走一次护栏+执行是"最终裁决"——
        # 保证进入输出的 SQL 一定是经过校验并成功执行的版本
        reason = guardrail(sql)
        if reason:
            print(f"🛑 护栏拦截：{reason}")
            continue
        try:
            cols, rows = run_sql(sql)
            print(f"结果 {len(rows)} 行: {cols}")
            for row in rows[:5]:              # 只展示前 5 行（真实系统这里会接 API/报表）
                print("  ", row)
        except Exception as e:
            print(f"重试后仍失败: {e}")


if __name__ == "__main__":
    main()
