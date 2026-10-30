import java.util.*;

/**
 * 专题 06：堆与 TopK
 * 包含三道经典题的实现：第 K 大元素、合并 K 个链表、数据流中位数
 */

// 链表节点定义（题 2 需要）
class ListNode {
    int val;
    ListNode next;
    ListNode(int val) { this.val = val; }
}

public class Solution {

    /**
     * 题 1：数组中的第 K 个最大元素（最小堆法）
     * 时间 O(n log k)，空间 O(k)
     */
    public static int findKthLargest(int[] nums, int k) {
        // 最小堆，维护 K 个最大元素
        PriorityQueue<Integer> minHeap = new PriorityQueue<>();
        for (int num : nums) {
            minHeap.offer(num);
            if (minHeap.size() > k) {
                minHeap.poll();  // 超过 K 个就弹出最小的
            }
        }
        return minHeap.peek();  // 堆顶就是第 K 大
    }

    /**
     * 题 2：合并 K 个升序链表
     * 时间 O(N log k)，空间 O(k)
     */
    public static ListNode mergeKLists(ListNode[] lists) {
        // 最小堆，按节点值排序
        PriorityQueue<ListNode> pq = new PriorityQueue<>((a, b) -> a.val - b.val);
        
        // 把所有链表的头节点入堆
        for (ListNode node : lists) {
            if (node != null) pq.offer(node);
        }
        
        ListNode dummy = new ListNode(0);
        ListNode curr = dummy;
        
        while (!pq.isEmpty()) {
            ListNode min = pq.poll();
            curr.next = min;
            curr = curr.next;
            // 把该链表的下一个节点入堆
            if (min.next != null) {
                pq.offer(min.next);
            }
        }
        return dummy.next;
    }

    /**
     * 题 3：数据流的中位数
     * addNum O(log n)，findMedian O(1)
     */
    static class MedianFinder {
        private PriorityQueue<Integer> left;   // 大顶堆，存较小的一半
        private PriorityQueue<Integer> right;  // 小顶堆，存较大的一半

        public MedianFinder() {
            left = new PriorityQueue<>((a, b) -> b - a);  // 大顶堆
            right = new PriorityQueue<>();                  // 小顶堆
        }

        public void addNum(int num) {
            // 先加到左边
            left.offer(num);
            // 如果左边最大值 > 右边最小值，需要调整
            if (!right.isEmpty() && left.peek() > right.peek()) {
                right.offer(left.poll());
            }
            // 平衡大小：left.size() == right.size() 或 left.size() == right.size() + 1
            if (left.size() > right.size() + 1) {
                right.offer(left.poll());
            } else if (right.size() > left.size()) {
                left.offer(right.poll());
            }
        }

        public double findMedian() {
            if (left.size() == right.size()) {
                return (left.peek() + right.peek()) / 2.0;
            } else {
                return left.peek();  // 奇数时左边多一个
            }
        }
    }

    // ========== 辅助方法 ==========
    private static ListNode buildList(int[] arr) {
        if (arr.length == 0) return null;
        ListNode head = new ListNode(arr[0]);
        ListNode curr = head;
        for (int i = 1; i < arr.length; i++) {
            curr.next = new ListNode(arr[i]);
            curr = curr.next;
        }
        return head;
    }

    private static String printList(ListNode head) {
        StringBuilder sb = new StringBuilder();
        while (head != null) {
            sb.append(head.val).append(" -> ");
            head = head.next;
        }
        sb.append("null");
        return sb.toString();
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        System.out.println("=== 题 1：第 K 大元素 ===");
        int[] nums = {3, 2, 1, 5, 6, 4};
        int k = 2;
        System.out.printf("输入: %s, k=%d → 第 %d 大: %d%n",
            Arrays.toString(nums), k, k, findKthLargest(nums, k));

        System.out.println("\n=== 题 2：合并 K 个链表 ===");
        ListNode[] lists = {
            buildList(new int[]{1, 4, 5}),
            buildList(new int[]{1, 3, 4}),
            buildList(new int[]{2, 6})
        };
        System.out.println("输入:");
        for (ListNode list : lists) {
            System.out.println("  " + printList(list));
        }
        ListNode merged = mergeKLists(lists);
        System.out.println("输出: " + printList(merged));

        System.out.println("\n=== 题 3：数据流中位数 ===");
        MedianFinder mf = new MedianFinder();
        mf.addNum(1);
        mf.addNum(2);
        System.out.println("addNum(1), addNum(2) → median = " + mf.findMedian());  // 1.5
        mf.addNum(3);
        System.out.println("addNum(3) → median = " + mf.findMedian());  // 2.0
    }
}
