#!/usr/bin/env python3
"""
Lab 06 — MCP（Model Context Protocol）最小实现：手写 JSON-RPC 工具服务器
=======================================================================

【MCP 是什么】
Anthropic 开放的协议，把"工具/资源"标准化暴露给任何模型客户端——
类比 USB-C：工具服务实现一次，所有支持 MCP 的客户端（Claude/Cursor/Cline...）都能用。

【协议核心（简化版，够你读懂真实 MCP）】
传输：stdio（标准输入输出）上跑 JSON-RPC 2.0
握手：客户端 → initialize → 服务端回 capabilities → initialized
用工具：客户端 → tools/list → 服务端回工具清单（含 JSON Schema）
       客户端 → tools/call {name, arguments} → 服务端执行并回结果

本文件实现：① 一个 MCP 工具服务器（stdio 模式）② 一个测试客户端（证明协议可用）
真实开发用官方 `mcp` python SDK（pip install mcp），但协议帧长这样——读懂这层，
SDK 的行为你全明白。

【运行】../.venv/bin/python mini_mcp.py --server   （作为服务器，读 stdin 写 stdout）
       ../.venv/bin/python mini_mcp.py --test     （自测：起服务器子进程跑完整握手+调用）
"""
import json
import os
import re
import subprocess
import sys

# 复用 Lab02 的工具注册表（MCP 服务器暴露的就是这些工具）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab02-tool-registry"))
from registry_agent import registry  # noqa: E402


# ---------------------------------------------------------------------------
# 服务器端：读一行 = 一个 JSON-RPC 请求，回一行 = 一个响应（行分隔帧，MCP 真实实现同理）
# ---------------------------------------------------------------------------

def handle_request(req: dict) -> dict:
    """MCP 方法路由：三种方法覆盖握手、发现、调用——真实 MCP 的核心子集。"""
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        # 握手：告诉客户端我是谁、我能做什么（协议版本 + 能力声明）
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mini-mcp", "version": "0.1.0"}}}

    if method == "tools/list":
        # 工具发现：返回与 OpenAI tools 规范一致的清单（Lab02 的 manifest 直接复用）
        tools = [{"name": n, "description": t["description"], "inputSchema": t["parameters"]}
                 for n, t in registry._tools.items()]
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    if method == "tools/call":
        # 工具调用：name + arguments → 执行 → 包装成 MCP 的 content 格式
        params = req.get("params", {})
        result = registry.execute(params.get("name", ""), params.get("arguments", {}))
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "content": [{"type": "text", "text": result}]}}

    return {"jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def serve():
    """服务器主循环：逐行读 stdin（每行一个请求），逐行写 stdout。"""
    print("mini-mcp server 已启动（stdin/stdout JSON-RPC）", file=sys.stderr)  # 日志走 stderr，不污染协议流
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            resp = handle_request(json.loads(line))
        except json.JSONDecodeError as e:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
        print(json.dumps(resp, ensure_ascii=False), flush=True)   # flush 关键：客户端在等这一行


# ---------------------------------------------------------------------------
# 测试客户端：起服务器子进程，完成"握手 → 发现 → 调用"全流程
# ---------------------------------------------------------------------------

def test():
    proc = subprocess.Popen(          # MCP stdio 模式的本质：客户端把服务器当子进程养着
        [sys.executable, os.path.abspath(__file__), "--server"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    def rpc(method: str, params: dict = None, req_id: int = 1) -> dict:
        req = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params:
            req["params"] = params
        proc.stdin.write(json.dumps(req) + "\n")   # 发请求（一行）
        proc.stdin.flush()
        return json.loads(proc.stdout.readline())  # 读响应（一行）

    info = rpc("initialize")
    print("① 握手:", info["result"]["serverInfo"])

    tools = rpc("tools/list", req_id=2)["result"]["tools"]
    print(f"② 发现 {len(tools)} 个工具:", [t["name"] for t in tools])

    call = rpc("tools/call", {"name": "calculate", "arguments": {"expression": "99*98"}}, req_id=3)
    print("③ 调用 calculate(99*98) →", call["result"]["content"][0]["text"])

    call2 = rpc("tools/call", {"name": "word_count", "arguments": {"text": "hello mcp world"}}, req_id=4)
    print("④ 调用 word_count →", call2["result"]["content"][0]["text"])

    proc.stdin.close()
    proc.wait()
    print("✅ MCP 协议全流程（握手/发现/调用）自测通过")


if __name__ == "__main__":
    if "--server" in sys.argv:
        serve()
    else:
        test()
