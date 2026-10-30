"""
布隆过滤器（Bloom Filter）
用途：快速判断元素"可能存在"或"一定不存在"
特点：假阳性（说存在可能不存在），无假阴性（说不存在一定不存在）
"""
import hashlib
from bitarray import bitarray


class BloomFilter:
    def __init__(self, size: int, hash_count: int):
        """
        :param size: bit 数组大小（越大误判率越低，内存越大）
        :param hash_count: 哈希函数个数（最优值 = (size/n) * ln2）
        """
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)

    def _hash(self, element: str, seed: int) -> int:
        """
        简单哈希函数（生产用 mmh3 等）
        通过 seed 参数模拟多个哈希函数
        """
        h = hashlib.md5(f"{element}{seed}".encode()).hexdigest()
        return int(h, 16)

    def add(self, element: str):
        """插入元素：用 hash_count 个哈希函数计算位置，全部置 1"""
        for i in range(self.hash_count):
            hash_val = self._hash(element, i)
            index = hash_val % self.size
            self.bit_array[index] = 1

    def might_contain(self, element: str) -> bool:
        """
        查询元素：检查 hash_count 个位置是否全为 1
        :return: True = 可能存在，False = 一定不存在
        """
        for i in range(self.hash_count):
            hash_val = self._hash(element, i)
            index = hash_val % self.size
            if not self.bit_array[index]:
                return False  # 有一个位置是 0，一定不存在
        return True  # 所有位置都是 1，可能存在（有误判）


# ========== 测试 ==========
if __name__ == "__main__":
    # 10 万元素，1% 误判率 → 约需 960 KB（约 100 万 bit），7 个哈希函数
    filter = BloomFilter(size=1_000_000, hash_count=7)

    print("=== 布隆过滤器演示 ===")
    filter.add("apple")
    filter.add("banana")
    filter.add("cherry")

    print(f"查询 'apple' → {filter.might_contain('apple')}")       # True
    print(f"查询 'banana' → {filter.might_contain('banana')}")     # True
    print(f"查询 'orange' → {filter.might_contain('orange')}")     # False（一定不存在）
    print(f"查询 'grape' → {filter.might_contain('grape')}")       # False 或 True（可能误判）

    # 批量测试误判率
    test_count = 10000
    false_positives = 0
    for i in range(test_count):
        test = f"test_{i}"
        if filter.might_contain(test):
            false_positives += 1
    print(f"\n误判率测试：查询 {test_count} 个未插入的元素，误判 {false_positives} 个（{false_positives * 100.0 / test_count:.2f}%）")
