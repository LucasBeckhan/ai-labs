"""
CountMinSketch 频率估计
用途：估计流式数据中元素的出现频率
特点：高估不低估（overestimate），误差与总流量成正比
"""
import hashlib


class CountMinSketch:
    def __init__(self, d: int, w: int):
        """
        :param d: 深度（哈希函数个数，越多误差越小）
        :param w: 宽度（每个哈希函数的范围，越大碰撞越少）
        """
        self.d = d
        self.w = w
        self.table = [[0] * w for _ in range(d)]

    def _hash(self, element: str, seed: int) -> int:
        """简单哈希（通过 seed 模拟多个哈希函数）"""
        h = hashlib.md5(f"{element}{seed}".encode()).hexdigest()
        return int(h, 16)

    def add(self, element: str, count: int = 1):
        """添加元素：d 个哈希函数各计算一个位置，对应位置 +count"""
        for i in range(self.d):
            hash_val = self._hash(element, i)
            index = hash_val % self.w
            self.table[i][index] += count

    def estimate(self, element: str) -> int:
        """查询频率：取 d 个位置的最小值（最小化碰撞影响）"""
        min_count = float('inf')
        for i in range(self.d):
            hash_val = self._hash(element, i)
            index = hash_val % self.w
            min_count = min(min_count, self.table[i][index])
        return min_count


# ========== 测试 ==========
if __name__ == "__main__":
    cms = CountMinSketch(d=5, w=1000)

    print("=== CountMinSketch 频率估计 ===")
    # 模拟流式数据
    stream = ["apple", "banana", "apple", "cherry", "apple", "banana", "apple"]
    for item in stream:
        cms.add(item)

    print("流数据: apple×4, banana×2, cherry×1")
    print(f"查询 'apple' 频率 → {cms.estimate('apple')}（实际 4）")
    print(f"查询 'banana' 频率 → {cms.estimate('banana')}（实际 2）")
    print(f"查询 'cherry' 频率 → {cms.estimate('cherry')}（实际 1）")
    print(f"查询 'grape' 频率 → {cms.estimate('grape')}（实际 0，可能高估）")

    # 大规模测试
    print("\n大规模测试：")
    cms2 = CountMinSketch(d=5, w=10000)
    for i in range(100000):
        cms2.add(f"item_{i % 100}")  # 100 个不同元素，每个约 1000 次
    
    estimated = cms2.estimate("item_50")
    print(f"实际频率: 1000, 估计频率: {estimated}, 误差: {estimated - 1000}")
