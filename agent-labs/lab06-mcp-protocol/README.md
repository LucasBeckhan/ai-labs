# Lab 06 — MCP 协议最小实现：手写 JSON-RPC 工具服务器

> **新版必做：[业务开发、生产故障与验收](BUSINESS-PRACTICE.md)**。原脚本是机制演示，旧“实测”仅指旧用例，不代表新增业务或生产就绪；以新版路线的边界和验收为准。

> **原示例边界校正：** mini_mcp.py固定2024-11-05且为简化教学子集，并非当前规范完整实现；缺少完整生命周期和通知处理。不能据此声称任何客户端兼容；新版请按锁定SDK/规范实现。



## 📖 本章学习指导
> 建议时长 **2 小时** ｜ 前置：agent Lab02 ｜ 关联面试：`interview-prep/06-llmops-ai-infra.md` Q14（MCP）

**学习循环：**
1. 读（20min）：handle_request 的三个方法路由（initialize/tools list/tools call）
2. 跑（20min）：`python mini_mcp.py --test` 看完整握手→发现→调用
3. 破坏练习（30min）：① 手动用管道发一帧：`echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python mini_mcp.py --server`；② 发一个不存在的方法看 -32601 错误；③ 加一个你自己的工具再 list
4. 验收自测：① MCP 解决什么问题（USB-C 类比）？② stdio 传输的本质（子进程 + 行分隔 JSON-RPC）？③ 为什么日志要走 stderr？
5. 产出：给 mini-mcp 加第 5 个工具并通过 --test

## 核心问答

**Q1：为什么要懂协议层？官方有 SDK。**

> ① SDK 出问题时你能定位到帧这一层；② 面试聊 MCP 能讲到 JSON-RPC/握手/能力协商，说明不是只会装包；③ 数据工程师的机会：把公司数据源封装成 MCP server（带护栏，见 Lab07），所有 AI 客户端立即可用。

**Q2：stdio 传输的本质是什么？为什么 MCP 选择它而不是 HTTP？**

> stdio 传输 = **子进程 + 行分隔 JSON-RPC**。客户端 spawn 一个子进程运行 MCP server，通过 stdin/stdout 通信，每行一个 JSON 帧。
>
> 选择 stdio 而非 HTTP 的原因：
> 1. **零配置**：不需要端口分配、不需要处理跨域、不需要 TLS 证书
> 2. **生命周期绑定**：客户端退出时子进程自动终止，没有"僵尸服务"
> 3. **本地优先**：MCP 的核心场景是本地工具调用（查数据库、读文件），不需要网络
>
> 代价：不能跨机器（只能本地），不适合云端 MCP server。生产环境如果要远程 MCP，会切换到 HTTP+SSE 传输（MCP 规范已定义）。

**Q3：为什么 MCP server 的日志必须走 stderr 而不是 stdout？**

> 因为 **stdout 是协议通道**——客户端从 stdout 读取 JSON-RPC 帧。如果日志也写 stdout，会破坏 JSON 解析（客户端收到非法 JSON 帧直接报错）。
>
> 这是 stdio 传输的硬性约束：
> - **stdout**：只能写 JSON-RPC 响应帧（`{"jsonrpc":"2.0",...}`）
> - **stderr**：写所有日志、调试信息、错误堆栈
>
> 本实验的 `mini_mcp.py` 里所有 `print(..., file=sys.stderr)` 都是这个原因。如果不小心用了 `print()`（默认 stdout），整个协议就崩了——这是新手实现 MCP server 最常见的坑。

## 实测记录
--test 全流程通过：握手 serverInfo ✓ / 发现 4 工具 ✓ / calculate(99*98)→**9702** ✓ / word_count→3 ✓

## 运行
```bash
cd ~/Documents/ai-labs/agent-labs/lab06-mcp-protocol
~/Documents/ai-labs/llmops-labs/.venv/bin/python mini_mcp.py --test
```
