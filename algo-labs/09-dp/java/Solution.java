import java.util.*;

/**
 * 专题 09：动态规划
 * 包含三道经典题的实现：爬楼梯、0-1 背包、最长递增子序列
 */
public class Solution {

    /**
     * 题 1：爬楼梯
     * 时间 O(n)，空间 O(1)（滚动数组优化）
     */
    public static int climbStairs(int n) {
        if (n <= 1) return 1;
        int prev2 = 1;  // dp[i-2]
        int prev1 = 1;  // dp[i-1]
        for (int i = 2; i <= n; i++) {
            int curr = prev1 + prev2;  // dp[i] = dp[i-1] + dp[i-2]
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    /**
     * 题 2：0-1 背包
     * 时间 O(nW)，空间 O(W)（滚动数组优化）
     */
    public static int knapsack(int[] weights, int[] values, int W) {
        int n = weights.length;
        int[] dp = new int[W + 1];
        
        // 遍历每个物品
        for (int i = 0; i < n; i++) {
            // 逆序遍历容量（0-1 背包的关键：每个物品只能选一次）
            for (int w = W; w >= weights[i]; w--) {
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }
        return dp[W];
    }

    /**
     * 题 3：最长递增子序列（O(n²) 解法）
     * 时间 O(n²)，空间 O(n)
     */
    public static int lengthOfLIS(int[] nums) {
        if (nums.length == 0) return 0;
        
        int[] dp = new int[nums.length];
        Arrays.fill(dp, 1);  // 每个元素自身构成长度为 1 的子序列
        
        int maxLen = 1;
        for (int i = 1; i < nums.length; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i]) {
                    dp[i] = Math.max(dp[i], dp[j] + 1);
                }
            }
            maxLen = Math.max(maxLen, dp[i]);
        }
        return maxLen;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        System.out.println("=== 题 1：爬楼梯 ===");
        for (int n : new int[]{1, 2, 3, 4, 5}) {
            System.out.printf("n=%d → %d 种方法%n", n, climbStairs(n));
        }

        System.out.println("\n=== 题 2：0-1 背包 ===");
        int[] weights = {2, 3, 4, 5};
        int[] values = {3, 4, 5, 6};
        int W = 5;
        System.out.printf("物品重量: %s, 价值: %s, 背包容量: %d%n",
            Arrays.toString(weights), Arrays.toString(values), W);
        System.out.printf("最大价值: %d%n", knapsack(weights, values, W));

        System.out.println("\n=== 题 3：最长递增子序列 ===");
        int[] nums1 = {10, 9, 2, 5, 3, 7, 101, 18};
        System.out.printf("输入: %s → LIS 长度: %d%n",
            Arrays.toString(nums1), lengthOfLIS(nums1));  // 4
        
        int[] nums2 = {0, 1, 0, 3, 2, 3};
        System.out.printf("输入: %s → LIS 长度: %d%n",
            Arrays.toString(nums2), lengthOfLIS(nums2));  // 4
    }
}
