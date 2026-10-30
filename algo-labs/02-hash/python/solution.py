"""
专题 02：哈希表
包含三道经典题的实现：Two Sum、字母异位词分组、最长无重复子串
"""
from collections import defaultdict


def two_sum(nums: list[int], target: int) -> list[int]:
    """
    题 1：Two Sum（无序数组）
    时间 O(n)，空间 O(n)
    """
    num_map = {}  # 值 -> 下标
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return [-1, -1]


def group_anagrams(strs: list[str]) -> list[list[str]]:
    """
    题 2：字母异位词分组
    时间 O(n * k log k)，空间 O(n * k)
    """
    anagram_map = defaultdict(list)
    for s in strs:
        # 排序后的字符串作为 key（异位词排序后相同）
        key = "".join(sorted(s))
        anagram_map[key].append(s)
    return list(anagram_map.values())


def length_of_longest_substring(s: str) -> int:
    """
    题 3：最长无重复字符子串
    时间 O(n)，空间 O(min(n, m))
    """
    window = set()
    left = 0
    max_len = 0
    for right in range(len(s)):
        while s[right] in window:
            window.remove(s[left])
            left += 1
        window.add(s[right])
        max_len = max(max_len, right - left + 1)
    return max_len


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 题 1：Two Sum ===")
    nums1 = [2, 7, 11, 15]
    res1 = two_sum(nums1, 9)
    print(f"输入: {nums1}, target=9 → 输出: {res1}")

    print("\n=== 题 2：字母异位词分组 ===")
    strs = ["eat", "tea", "tan", "ate", "nat", "bat"]
    groups = group_anagrams(strs)
    print(f"输入: {strs}")
    print("输出:")
    for group in groups:
        print(f"  {group}")

    print("\n=== 题 3：最长无重复子串 ===")
    s = "abcabcbb"
    length = length_of_longest_substring(s)
    print(f'输入: "{s}" → 最长无重复子串长度: {length}')
