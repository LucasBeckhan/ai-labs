
/**
 * 专题 01：数组与双指针
 * 包含三道经典题的实现：Two Sum II、盛最多水的容器、有序数组去重
 */
public class Solution {

    /**
     * 题 1：Two Sum II（有序数组）
     * 时间 O(n)，空间 O(1)
     */
    public static int[] twoSum(int[] numbers, int target) {
        int left = 0, right = numbers.length - 1;
        while (left < right) {
            int sum = numbers[left] + numbers[right];
            if (sum == target) {
                return new int[]{left + 1, right + 1}; // 1-based
            } else if (sum < target) {
                left++;  // 和太小，左指针右移
            } else {
                right--; // 和太大，右指针左移
            }
        }
        return new int[]{-1, -1};
    }

    /**
     * 题 2：盛最多水的容器
     * 时间 O(n)，空间 O(1)
     * 关键：每次移动较矮的那根柱子
     */
    public static int maxArea(int[] height) {
        int left = 0, right = height.length - 1;
        int maxWater = 0;
        while (left < right) {
            int h = Math.min(height[left], height[right]);
            int width = right - left;
            maxWater = Math.max(maxWater, h * width);
            // 移动较矮的柱子
            if (height[left] < height[right]) {
                left++;
            } else {
                right--;
            }
        }
        return maxWater;
    }

    /**
     * 题 3：有序数组去重（原地）
     * 时间 O(n)，空间 O(1)
     * 返回新长度，前 length 个元素无重复
     */
    public static int removeDuplicates(int[] nums) {
        if (nums.length == 0) return 0;
        int i = 1; // 慢指针：下一个要写的位置
        for (int j = 1; j < nums.length; j++) { // 快指针：遍历
            if (nums[j] != nums[i - 1]) {
                nums[i] = nums[j];
                i++;
            }
        }
        return i;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        System.out.println("=== 题 1：Two Sum II ===");
        int[] nums1 = {2, 7, 11, 15};
        int[] res1 = twoSum(nums1, 9);
        System.out.printf("输入: [2,7,11,15], target=9 → 输出: [%d, %d]%n", res1[0], res1[1]);

        System.out.println("\n=== 题 2：盛最多水的容器 ===");
        int[] height = {1, 8, 6, 2, 5, 4, 8, 3, 7};
        int area = maxArea(height);
        System.out.printf("输入: [1,8,6,2,5,4,8,3,7] → 最大面积: %d%n", area);

        System.out.println("\n=== 题 3：有序数组去重 ===");
        int[] nums3 = {1, 1, 2, 2, 3, 4, 4, 5};
        int len = removeDuplicates(nums3);
        System.out.printf("输入: [1,1,2,2,3,4,4,5] → 新长度: %d, 数组: ", len);
        for (int i = 0; i < len; i++) {
            System.out.printf("%d ", nums3[i]);
        }
        System.out.println();
    }
}
