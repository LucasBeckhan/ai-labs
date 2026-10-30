#!/usr/bin/env python3
"""
Lab 07 — Agent 评估与安全：护栏 + 回归测试
==========================================

Agent 上线前必须回答两个问题：
  ① 安全：恶意/越界输入会不会造成破坏？（工具滥用、注入、无限循环）
  ② 质量：正常任务的成功率是多少？改了提示词/模型后有没有变差？（回归）

本实验给 Lab02 的注册表 Agent 建一套最小"安全测试 + 回归测试"：
  安全组（应全部被拦/降级）：
    - 越界工具调用（不存在的工具）
    - 危险表达式注入（calculate 里塞 import）
    - 超范围参数（密码长度 9999）
  回归组（应全部成功）：
    - 正常计算 / 字数统计

运行即测试：任何一项失败打印 FAIL 并以非零码退出（CI 可直接用）。

【运行】../.venv/bin/python eval_safety.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab02-tool-registry"))
from registry_agent import registry  # noqa: E402

PASSED, FAILED = 0, 0

def check(name: str, condition: bool, detail: str = ""):
    """断言辅助：统一计数与输出（测试框架的雏形——为什么不用 pytest 见 README）。"""
    global PASSED, FAILED
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {name}" + (f"  → {detail[:60]}" if detail and not condition else ""))
    PASSED, FAILED = PASSED + (condition), FAILED + (not condition)


print("== 安全测试组：恶意输入必须被拦截 ==")

# 1) 危险表达式注入：白名单应拒绝（__import__ 含字母外的字符其实会过白名单？
#    不会——白名单只放行数字和运算符，字母直接被拒）
r = registry.execute("calculate", {"expression": "__import__('os').system('rm -rf /')"})
check("计算器注入被拦截", r.startswith("错误"), r)

# 2) 不存在的工具（模拟模型幻觉出的工具名）
r = registry.execute("run_shell", {"cmd": "ls"})
check("幻觉工具被拒绝", "不存在" in r, r)

# 3) 参数范围裁剪：密码长度 9999 应被压回 32 以内
r = registry.execute("gen_password", {"length": 9999})
check("超范围参数被裁剪", 6 <= len(r) <= 32 and "错误" not in r, r)

# 4) 缺必填参数：返回可读错误而不是崩溃
r = registry.execute("calculate", {})
check("缺参返回可读错误", "缺少必填参数" in r, r)

# 5) 类型错误：模型传字符串给 float 参数，宽容转换失败时应报错
r = registry.execute("c_to_f", {"celsius": "很热"})
check("非法类型被拒绝", "错误" in r, r)

print("\n== 回归测试组：正常功能不受护栏误伤 ==")

r = registry.execute("calculate", {"expression": "(100+200)*3"})
check("正常计算", r == "900", r)

r = registry.execute("word_count", {"text": "hello 世界"})
check("中英混合统计", r == "中文字数=2, 英文单词数=1", r)

r = registry.execute("c_to_f", {"celsius": "100"})   # 字符串数字应被宽容转换
check("字符串数字宽容转换", "212" in r, r)

print(f"\n结果: {PASSED} 通过, {FAILED} 失败")
sys.exit(0 if FAILED == 0 else 1)
