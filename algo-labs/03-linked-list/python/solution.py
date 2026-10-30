"""
专题 03：链表
包含三道经典题的实现：反转链表、合并两个有序链表、环形链表
"""


class ListNode:
    """链表节点定义"""
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reverse_list(head: ListNode) -> ListNode:
    """
    题 1：反转链表（迭代法）
    时间 O(n)，空间 O(1)
    """
    prev = None
    curr = head
    while curr:
        next_node = curr.next  # 保存下一个节点
        curr.next = prev       # 反转指针
        prev = curr            # prev 前移
        curr = next_node       # curr 前移
    return prev  # prev 就是新的头节点


def merge_two_lists(l1: ListNode, l2: ListNode) -> ListNode:
    """
    题 2：合并两个有序链表
    时间 O(n+m)，空间 O(1)
    """
    dummy = ListNode(0)  # 虚拟头节点
    curr = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next
    # 接上剩余部分
    curr.next = l1 if l1 else l2
    return dummy.next


def has_cycle(head: ListNode) -> bool:
    """
    题 3：环形链表（快慢指针）
    时间 O(n)，空间 O(1)
    """
    if not head or not head.next:
        return False
    slow = head
    fast = head.next
    while slow != fast:
        if not fast or not fast.next:
            return False
        slow = slow.next       # 慢指针走 1 步
        fast = fast.next.next  # 快指针走 2 步
    return True  # 相遇说明有环


# ========== 辅助函数 ==========
def build_list(arr: list[int]) -> ListNode:
    """从数组构造链表"""
    if not arr:
        return None
    head = ListNode(arr[0])
    curr = head
    for val in arr[1:]:
        curr.next = ListNode(val)
        curr = curr.next
    return head


def print_list(head: ListNode) -> str:
    """打印链表"""
    result = []
    while head:
        result.append(str(head.val))
        head = head.next
    return " -> ".join(result) + " -> null"


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 题 1：反转链表 ===")
    list1 = build_list([1, 2, 3, 4, 5])
    print(f"输入: {print_list(list1)}")
    reversed_list = reverse_list(list1)
    print(f"输出: {print_list(reversed_list)}")

    print("\n=== 题 2：合并两个有序链表 ===")
    l1 = build_list([1, 2, 4])
    l2 = build_list([1, 3, 4])
    print(f"输入: {print_list(l1)}")
    print(f"      {print_list(l2)}")
    merged = merge_two_lists(l1, l2)
    print(f"输出: {print_list(merged)}")

    print("\n=== 题 3：环形链表 ===")
    cycle = build_list([3, 2, 0, -4])
    cycle.next.next.next.next = cycle.next  # 制造环：尾节点指向第二个节点
    has = has_cycle(cycle)
    print("输入: 3->2->0->-4->(回到 2)")
    print(f"输出: {has}")

    no_cycle = build_list([1, 2, 3])
    no_has = has_cycle(no_cycle)
    print(f"输入: {print_list(no_cycle)}")
    print(f"输出: {no_has}")
