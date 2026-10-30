"""
滑动窗口去重
用途：流式数据中只保留最近 N 个元素内的去重
特点：插入 O(1)，查询 O(1)，空间 O(N)
"""
from collections import deque


class SlidingWindowDedup:
    def __init__(self, max_size: int):
        """
        :param max_size: 窗口最大容量
        """
        self.window = deque()  # 队列维护窗口内的元素顺序
        self.seen = set()      # HashSet 快速判断重复
        self.max_size = max_size

    def add(self, element: str) -> bool:
        """
        尝试添加元素（如果窗口内已存在则拒绝）
        :return: True = 添加成功，False = 重复被拒绝
        """
        if element in self.seen:
            return False  # 窗口内已存在，拒绝

        # 窗口满了，移除最老的元素
        if len(self.window) >= self.max_size:
            oldest = self.window.popleft()
            self.seen.remove(oldest)

        # 添加新元素
        self.window.append(element)
        self.seen.add(element)
        return True

    def contains(self, element: str) -> bool:
        """查询元素是否在窗口内"""
        return element in self.seen

    def size(self) -> int:
        """获取当前窗口大小"""
        return len(self.window)


# ========== 测试 ==========
if __name__ == "__main__":
    dedup = SlidingWindowDedup(max_size=5)

    print("=== 滑动窗口去重（窗口大小 5）===")
    stream = ["A", "B", "C", "A", "D", "E", "B", "F"]
    
    for item in stream:
        added = dedup.add(item)
        status = "成功" if added else "重复"
        print(f"添加 '{item}' → {status}, 窗口: {list(dedup.window)}")

    print(f"\n最终窗口内容: {list(dedup.window)}")
    print(f"查询 'A' 是否在窗口内 → {dedup.contains('A')}")
    print(f"查询 'B' 是否在窗口内 → {dedup.contains('B')}")
