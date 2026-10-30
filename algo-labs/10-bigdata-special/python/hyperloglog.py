import hashlib
import math

class HyperLogLog:
    def __init__(self, p=10):
        self.p = p
        self.m = 1 << p  # 寄存器数量 = 2^p
        self.registers = [0] * self.m

    def _hash(self, element: str) -> int:
        """FNV-1a 哈希（更好的分布）"""
        hash_val = 0x811c9dc5  # FNV offset basis
        for char in element:
            hash_val ^= ord(char)
            hash_val = (hash_val * 0x01000193) & 0xFFFFFFFF  # FNV prime，保持 32 位
        return hash_val

    def add(self, element: str):
        """添加元素：哈希后取前 p 位作为索引，剩余位计算前导零"""
        hash_val = self._hash(element)
        index = hash_val >> (32 - self.p)  # 取高 p 位作为索引
        remaining = hash_val & ((1 << (32 - self.p)) - 1)  # 剩余位
        
        # 计算 remaining 中从高位开始第一个 1 出现的位置（1-based）
        leading_zeros = 1
        if remaining == 0:
            leading_zeros = 32 - self.p + 1  # 全是 0，位置在最后
        else:
            # 找到第一个 1 的位置
            mask = 1 << (31 - self.p)
            while (remaining & mask) == 0:
                leading_zeros += 1
                mask >>= 1
                if mask == 0:
                    break
        
        self.registers[index] = max(self.registers[index], leading_zeros)

    def estimate(self) -> int:
        """估算基数"""
        # 调和平均数
        sum_inv = sum(2 ** (-val) for val in self.registers)
        alpha = self._get_alpha()
        estimate = alpha * self.m * self.m / sum_inv

        # 小范围修正（线性计数）
        zeros = self.registers.count(0)
        if estimate <= 2.5 * self.m and zeros > 0:
            estimate = self.m * math.log(self.m / zeros)

        return int(estimate)

    def _get_alpha(self) -> float:
        """校正系数"""
        if self.m == 16:
            return 0.673
        elif self.m == 32:
            return 0.697
        elif self.m == 64:
            return 0.709
        else:
            return 0.7213 / (1 + 1.079 / self.m)

if __name__ == "__main__":
    hll = HyperLogLog(p=10)  # 1024 个寄存器
    actual = set()

    print("=== HyperLogLog 基数估计 ===")
    for i in range(100000):
        element = f"user_{i}"
        hll.add(element)
        actual.add(element)

    estimated = hll.estimate()
    actual_size = len(actual)
    error = abs(estimated - actual_size) * 100.0 / actual_size

    print(f"实际基数: {actual_size}")
    print(f"估计基数: {estimated}")
    print(f"误差: {error:.2f}%")
