import java.util.*;

/**
 * 专题 07：二分查找
 * 包含三道经典题的实现：二分查找、旋转数组最小值、查找元素的第一个和最后一个位置
 */
public class Solution {

    /**
     * 题 1：二分查找
     * 时间 O(log n)，空间 O(1)
     */
    public static int search(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;  // 防溢出
            if (nums[mid] == target) {
                return mid;
            } else if (nums[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return -1;
    }

    /**
     * 题 2：寻找旋转排序数组中的最小值
     * 时间 O(log n)，空间 O(1)
     */
    public static int findMin(int[] nums) {
        int left = 0, right = nums.length - 1;
        while (left < right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] > nums[right]) {
                // 最小值在右半部分
                left = mid + 1;
            } else {
                // 最小值在左半部分或就是 mid
                right = mid;
            }
        }
        return nums[left];
    }

    /**
     * 题 3：在排序数组中查找元素的第一个和最后一个位置
     * 时间 O(log n)，空间 O(1)
     */
    public static int[] searchRange(int[] nums, int target) {
        int first = findFirst(nums, target);
        int last = findLast(nums, target);
        return new int[]{first, last};
    }

    // 找第一个 >= target 的位置
    private static int findFirst(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        int result = -1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] >= target) {
                if (nums[mid] == target) result = mid;
                right = mid - 1;  // 继续向左找
            } else {
                left = mid + 1;
            }
        }
        return result;
    }

    // 找最后一个 <= target 的位置
    private static int findLast(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        int result = -1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] <= target) {
                if (nums[mid] == target) result = mid;
                left = mid + 1;  // 继续向右找
            } else {
                right = mid - 1;
            }
        }
        return result;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        System.out.println("=== 题 1：二分查找 ===");
        int[] nums1 = {-1, 0, 3, 5, 9, 12};
        System.out.printf("输入: %s, target=9 → 输出: %d%n",
            Arrays.toString(nums1), search(nums1, 9));
        System.out.printf("输入: %s, target=2 → 输出: %d%n",
            Arrays.toString(nums1), search(nums1, 2));

        System.out.println("\n=== 题 2：旋转数组最小值 ===");
        int[] nums2 = {4, 5, 6, 7, 0, 1, 2};
        System.out.printf("输入: %s → 最小值: %d%n",
            Arrays.toString(nums2), findMin(nums2));
        int[] nums2b = {1, 2, 3, 4, 5};  // 没旋转
        System.out.printf("输入: %s → 最小值: %d%n",
            Arrays.toString(nums2b), findMin(nums2b));

        System.out.println("\n=== 题 3：查找第一个和最后一个位置 ===");
        int[] nums3 = {5, 7, 7, 8, 8, 10};
        int[] range1 = searchRange(nums3, 8);
        System.out.printf("输入: %s, target=8 → 输出: [%d, %d]%n",
            Arrays.toString(nums3), range1[0], range1[1]);
        int[] range2 = searchRange(nums3, 6);
        System.out.printf("输入: %s, target=6 → 输出: [%d, %d]%n",
            Arrays.toString(nums3), range2[0], range2[1]);
    }
}
