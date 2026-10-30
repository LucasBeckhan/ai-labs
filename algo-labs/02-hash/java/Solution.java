import java.util.*;

/**
 * 专题 02：哈希表
 * 包含三道经典题的实现：Two Sum、字母异位词分组、最长无重复子串
 */
public class Solution {

    /**
     * 题 1：Two Sum（无序数组）
     * 时间 O(n)，空间 O(n)
     */
    public static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>(); // 值 -> 下标
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[]{map.get(complement), i};
            }
            map.put(nums[i], i);
        }
        return new int[]{-1, -1};
    }

    /**
     * 题 2：字母异位词分组
     * 时间 O(n * k log k)，空间 O(n * k)
     */
    public static List<List<String>> groupAnagrams(String[] strs) {
        Map<String, List<String>> map = new HashMap<>();
        for (String s : strs) {
            // 排序后的字符串作为 key（异位词排序后相同）
            char[] chars = s.toCharArray();
            Arrays.sort(chars);
            String key = new String(chars);
            map.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
        }
        return new ArrayList<>(map.values());
    }

    /**
     * 题 3：最长无重复字符子串
     * 时间 O(n)，空间 O(min(n, m))
     */
    public static int lengthOfLongestSubstring(String s) {
        Set<Character> window = new HashSet<>();
        int left = 0, maxLen = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            while (window.contains(c)) {
                window.remove(s.charAt(left));
                left++;
            }
            window.add(c);
            maxLen = Math.max(maxLen, right - left + 1);
        }
        return maxLen;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        System.out.println("=== 题 1：Two Sum ===");
        int[] nums1 = {2, 7, 11, 15};
        int[] res1 = twoSum(nums1, 9);
        System.out.printf("输入: [2,7,11,15], target=9 → 输出: [%d, %d]%n", res1[0], res1[1]);

        System.out.println("\n=== 题 2：字母异位词分组 ===");
        String[] strs = {"eat", "tea", "tan", "ate", "nat", "bat"};
        List<List<String>> groups = groupAnagrams(strs);
        System.out.println("输入: " + Arrays.toString(strs));
        System.out.println("输出:");
        for (List<String> group : groups) {
            System.out.println("  " + group);
        }

        System.out.println("\n=== 题 3：最长无重复子串 ===");
        String s = "abcabcbb";
        int len = lengthOfLongestSubstring(s);
        System.out.printf("输入: \"%s\" → 最长无重复子串长度: %d%n", s, len);
    }
}
