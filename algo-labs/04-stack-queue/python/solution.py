"""
专题 04：栈与队列
包含三道经典题的实现：有效括号、最小栈、每日温度
"""


def is_valid(s: str) -> bool:
    """
    题 1：有效的括号
    时间 O(n)，空间 O(n)
    """
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in mapping:
            # 右括号：检查栈顶是否匹配
            if not stack or stack[-1] != mapping[char]:
                return False
            stack.pop()
        else:
            # 左括号：压栈
            stack.append(char)
    return len(stack) == 0


class MinStack:
    """
    题 2：最小栈
    所有操作 O(1)
    """
    def __init__(self):
        self.main_stack = []
        self.min_stack = []  # 辅助栈存当前最小值

    def push(self, val: int) -> None:
        self.main_stack.append(val)
        # 辅助栈压入 min(新元素, 当前最小)
        if not self.min_stack:
            self.min_stack.append(val)
        else:
            self.min_stack.append(min(val, self.min_stack[-1]))

    def pop(self) -> None:
        self.main_stack.pop()
        self.min_stack.pop()

    def top(self) -> int:
        return self.main_stack[-1]

    def get_min(self) -> int:
        return self.min_stack[-1]


def daily_temperatures(temperatures: list[int]) -> list[int]:
    """
    题 3：每日温度（单调栈）
    时间 O(n)，空间 O(n)
    """
    n = len(temperatures)
    result = [0] * n
    stack = []  # 存下标，对应温度递减

    for i in range(n):
        # 当前温度 > 栈顶温度，说明栈顶找到了"下一个更高"
        while stack and temperatures[i] > temperatures[stack[-1]]:
            prev = stack.pop()
            result[prev] = i - prev  # 天数差
        stack.append(i)
    return result


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 题 1：有效的括号 ===")
    print(f'输入: "()" → 输出: {is_valid("()")}')
    print(f'输入: "()[]{{}}" → 输出: {is_valid("()[]{}")}')
    print(f'输入: "(]" → 输出: {is_valid("(]")}')
    print(f'输入: "([)]" → 输出: {is_valid("([)]")}')

    print("\n=== 题 2：最小栈 ===")
    min_stack = MinStack()
    min_stack.push(-2)
    min_stack.push(0)
    min_stack.push(-3)
    print("push(-2), push(0), push(-3)")
    print(f"get_min() → {min_stack.get_min()}")  # -3
    min_stack.pop()
    print("pop()")
    print(f"top() → {min_stack.top()}")  # 0
    print(f"get_min() → {min_stack.get_min()}")  # -2

    print("\n=== 题 3：每日温度 ===")
    temps = [73, 74, 75, 71, 69, 72, 76, 73]
    days = daily_temperatures(temps)
    print(f"输入: {temps}")
    print(f"输出: {days}")
