"""
专题 09：动态规划
包含三道经典题的实现：爬楼梯、0-1 背包、最长递增子序列
"""


def climb_stairs(n: int) -> int:
    """
    题 1：爬楼梯
    时间 O(n)，空间 O(1)（滚动数组优化）
    """
    if n <= 1:
        return 1
    prev2 = 1  # dp[i-2]
    prev1 = 1  # dp[i-1]
    for i in range(2, n + 1):
        curr = prev1 + prev2  # dp[i] = dp[i-1] + dp[i-2]
        prev2 = prev1
        prev1 = curr
    return prev1


def knapsack(weights: list[int], values: list[int], W: int) -> int:
    """
    题 2：0-1 背包
    时间 O(nW)，空间 O(W)（滚动数组优化）
    """
    n = len(weights)
    dp = [0] * (W + 1)
    
    # 遍历每个物品
    for i in range(n):
        # 逆序遍历容量（0-1 背包的关键：每个物品只能选一次）
        for w in range(W, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[W]


def length_of_lis(nums: list[int]) -> int:
    """
    题 3：最长递增子序列（O(n²) 解法）
    时间 O(n²)，空间 O(n)
    """
    if not nums:
        return 0
    
    dp = [1] * len(nums)  # 每个元素自身构成长度为 1 的子序列
    
    max_len = 1
    for i in range(1, len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
        max_len = max(max_len, dp[i])
    
    return max_len


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 题 1：爬楼梯 ===")
    for n in [1, 2, 3, 4, 5]:
        print(f"n={n} → {climb_stairs(n)} 种方法")

    print("\n=== 题 2：0-1 背包 ===")
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    W = 5
    print(f"物品重量: {weights}, 价值: {values}, 背包容量: {W}")
    print(f"最大价值: {knapsack(weights, values, W)}")

    print("\n=== 题 3：最长递增子序列 ===")
    nums1 = [10, 9, 2, 5, 3, 7, 101, 18]
    print(f"输入: {nums1} → LIS 长度: {length_of_lis(nums1)}")  # 4
    
    nums2 = [0, 1, 0, 3, 2, 3]
    print(f"输入: {nums2} → LIS 长度: {length_of_lis(nums2)}")  # 4
