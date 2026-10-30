"""
专题 01：数组与双指针
包含三道经典题的实现：Two Sum II、盛最多水的容器、有序数组去重
"""


def two_sum(numbers: list[int], target: int) -> list[int]:
    """
    题 1：Two Sum II（有序数组）
    时间 O(n)，空间 O(1)
    """
    left, right = 0, len(numbers) - 1
    while left < right:
        s = numbers[left] + numbers[right]
        if s == target:
            return [left + 1, right + 1]  # 1-based
        elif s < target:
            left += 1  # 和太小，左指针右移
        else:
            right -= 1  # 和太大，右指针左移
    return [-1, -1]


def max_area(height: list[int]) -> int:
    """
    题 2：盛最多水的容器
    时间 O(n)，空间 O(1)
    关键：每次移动较矮的那根柱子
    """
    left, right = 0, len(height) - 1
    max_water = 0
    while left < right:
        h = min(height[left], height[right])
        width = right - left
        max_water = max(max_water, h * width)
        # 移动较矮的柱子
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return max_water


def remove_duplicates(nums: list[int]) -> int:
    """
    题 3：有序数组去重（原地）
    时间 O(n)，空间 O(1)
    返回新长度，前 length 个元素无重复
    """
    if not nums:
        return 0
    i = 1  # 慢指针：下一个要写的位置
    for j in range(1, len(nums)):  # 快指针：遍历
        if nums[j] != nums[i - 1]:
            nums[i] = nums[j]
            i += 1
    return i


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 题 1：Two Sum II ===")
    nums1 = [2, 7, 11, 15]
    res1 = two_sum(nums1, 9)
    print(f"输入: {nums1}, target=9 → 输出: {res1}")

    print("\n=== 题 2：盛最多水的容器 ===")
    height = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    area = max_area(height)
    print(f"输入: {height} → 最大面积: {area}")

    print("\n=== 题 3：有序数组去重 ===")
    nums3 = [1, 1, 2, 2, 3, 4, 4, 5]
    length = remove_duplicates(nums3)
    print(f"输入: [1,1,2,2,3,4,4,5] → 新长度: {length}, 数组: {nums3[:length]}")
