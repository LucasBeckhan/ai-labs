"""
专题 07：二分查找
包含三道经典题的实现：二分查找、旋转数组最小值、查找元素的第一个和最后一个位置
"""


def search(nums: list[int], target: int) -> int:
    """
    题 1：二分查找
    时间 O(log n)，空间 O(1)
    """
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2  # 防溢出
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def find_min(nums: list[int]) -> int:
    """
    题 2：寻找旋转排序数组中的最小值
    时间 O(log n)，空间 O(1)
    """
    left, right = 0, len(nums) - 1
    while left < right:
        mid = left + (right - left) // 2
        if nums[mid] > nums[right]:
            # 最小值在右半部分
            left = mid + 1
        else:
            # 最小值在左半部分或就是 mid
            right = mid
    return nums[left]


def search_range(nums: list[int], target: int) -> list[int]:
    """
    题 3：在排序数组中查找元素的第一个和最后一个位置
    时间 O(log n)，空间 O(1)
    """
    first = find_first(nums, target)
    last = find_last(nums, target)
    return [first, last]


def find_first(nums: list[int], target: int) -> int:
    """找第一个 >= target 的位置"""
    left, right = 0, len(nums) - 1
    result = -1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] >= target:
            if nums[mid] == target:
                result = mid
            right = mid - 1  # 继续向左找
        else:
            left = mid + 1
    return result


def find_last(nums: list[int], target: int) -> int:
    """找最后一个 <= target 的位置"""
    left, right = 0, len(nums) - 1
    result = -1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] <= target:
            if nums[mid] == target:
                result = mid
            left = mid + 1  # 继续向右找
        else:
            right = mid - 1
    return result


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 题 1：二分查找 ===")
    nums1 = [-1, 0, 3, 5, 9, 12]
    print(f"输入: {nums1}, target=9 → 输出: {search(nums1, 9)}")
    print(f"输入: {nums1}, target=2 → 输出: {search(nums1, 2)}")

    print("\n=== 题 2：旋转数组最小值 ===")
    nums2 = [4, 5, 6, 7, 0, 1, 2]
    print(f"输入: {nums2} → 最小值: {find_min(nums2)}")
    nums2b = [1, 2, 3, 4, 5]  # 没旋转
    print(f"输入: {nums2b} → 最小值: {find_min(nums2b)}")

    print("\n=== 题 3：查找第一个和最后一个位置 ===")
    nums3 = [5, 7, 7, 8, 8, 10]
    range1 = search_range(nums3, 8)
    print(f"输入: {nums3}, target=8 → 输出: {range1}")
    range2 = search_range(nums3, 6)
    print(f"输入: {nums3}, target=6 → 输出: {range2}")
