/**
 * 专题 03：链表
 * 包含三道经典题的实现：反转链表、合并两个有序链表、环形链表
 */

// 链表节点定义
class ListNode {
    int val;
    ListNode next;
    ListNode(int val) { this.val = val; }
}

public class Solution {

    /**
     * 题 1：反转链表（迭代法）
     * 时间 O(n)，空间 O(1)
     */
    public static ListNode reverseList(ListNode head) {
        ListNode prev = null;
        ListNode curr = head;
        while (curr != null) {
            ListNode next = curr.next;  // 保存下一个节点
            curr.next = prev;           // 反转指针
            prev = curr;                // prev 前移
            curr = next;                // curr 前移
        }
        return prev;  // prev 就是新的头节点
    }

    /**
     * 题 2：合并两个有序链表
     * 时间 O(n+m)，空间 O(1)
     */
    public static ListNode mergeTwoLists(ListNode l1, ListNode l2) {
        ListNode dummy = new ListNode(0);  // 虚拟头节点
        ListNode curr = dummy;
        while (l1 != null && l2 != null) {
            if (l1.val <= l2.val) {
                curr.next = l1;
                l1 = l1.next;
            } else {
                curr.next = l2;
                l2 = l2.next;
            }
            curr = curr.next;
        }
        // 接上剩余部分
        curr.next = (l1 != null) ? l1 : l2;
        return dummy.next;
    }

    /**
     * 题 3：环形链表（快慢指针）
     * 时间 O(n)，空间 O(1)
     */
    public static boolean hasCycle(ListNode head) {
        if (head == null || head.next == null) return false;
        ListNode slow = head;
        ListNode fast = head.next;
        while (slow != fast) {
            if (fast == null || fast.next == null) return false;
            slow = slow.next;        // 慢指针走 1 步
            fast = fast.next.next;   // 快指针走 2 步
        }
        return true;  // 相遇说明有环
    }

    // ========== 辅助方法 ==========
    // 从数组构造链表
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

    // 打印链表
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
        System.out.println("=== 题 1：反转链表 ===");
        ListNode list1 = buildList(new int[]{1, 2, 3, 4, 5});
        System.out.println("输入: " + printList(list1));
        ListNode reversed = reverseList(list1);
        System.out.println("输出: " + printList(reversed));

        System.out.println("\n=== 题 2：合并两个有序链表 ===");
        ListNode l1 = buildList(new int[]{1, 2, 4});
        ListNode l2 = buildList(new int[]{1, 3, 4});
        System.out.println("输入: " + printList(l1));
        System.out.println("      " + printList(l2));
        ListNode merged = mergeTwoLists(l1, l2);
        System.out.println("输出: " + printList(merged));

        System.out.println("\n=== 题 3：环形链表 ===");
        ListNode cycle = buildList(new int[]{3, 2, 0, -4});
        cycle.next.next.next.next = cycle.next;  // 制造环：尾节点指向第二个节点
        boolean hasCycle = hasCycle(cycle);
        System.out.println("输入: 3->2->0->-4->(回到 2)");
        System.out.println("输出: " + hasCycle);

        ListNode noCycle = buildList(new int[]{1, 2, 3});
        boolean noHasCycle = hasCycle(noCycle);
        System.out.println("输入: " + printList(noCycle));
        System.out.println("输出: " + noHasCycle);
    }
}
