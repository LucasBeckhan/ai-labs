"""
专题 06：堆与 TopK
包含三道经典题的实现：第 K 大元素、合并 K 个链表、数据流中位数
"""
import heapq


class ListNode:
    """链表节点定义"""
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    # 为了 heapq 能比较节点
    def __lt__(self, other):
        return self.val < other.val


def find_kth_largest(nums: list[int], k: int) -> int:
    """
    题 1：数组中的第 K 个最大元素（最小堆法）
    时间 O(n log k)，空间 O(k)
    """
    # Python 的 heapq 是最小堆
    min_heap = []
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)  # 超过 K 个就弹出最小的
    return min_heap[0]  # 堆顶就是第 K 大


def merge_k_lists(lists: list[ListNode]) -> ListNode:
    """
    题 2：合并 K 个升序链表
    时间 O(N log k)，空间 O(k)
    """
    # 最小堆，存所有链表的头节点
    heap = []
    for i, node in enumerate(lists):
        if node:
            # (值, 索引, 节点) - 索引用于打破值相同时的比较
            heapq.heappush(heap, (node.val, i, node))
    
    dummy = ListNode(0)
    curr = dummy
    idx = len(lists)  # 用于生成唯一索引
    
    while heap:
        val, _, min_node = heapq.heappop(heap)
        curr.next = min_node
        curr = curr.next
        # 把该链表的下一个节点入堆
        if min_node.next:
            heapq.heappush(heap, (min_node.next.val, idx, min_node.next))
            idx += 1
    
    return dummy.next


class MedianFinder:
    """
    题 3：数据流的中位数
    add_num O(log n)，find_median O(1)
    """
    def __init__(self):
        self.left = []   # 大顶堆（存负数），存较小的一半
        self.right = []  # 小顶堆，存较大的一半

    def add_num(self, num: int) -> None:
        # 先加到左边
        heapq.heappush(self.left, -num)
        # 如果左边最大值 > 右边最小值，需要调整
        if self.right and -self.left[0] > self.right[0]:
            heapq.heappush(self.right, -heapq.heappop(self.left))
        # 平衡大小：left.size() == right.size() 或 left.size() == right.size() + 1
        if len(self.left) > len(self.right) + 1:
            heapq.heappush(self.right, -heapq.heappop(self.left))
        elif len(self.right) > len(self.left):
            heapq.heappush(self.left, -heapq.heappop(self.right))

    def find_median(self) -> float:
        if len(self.left) == len(self.right):
            return (-self.left[0] + self.right[0]) / 2.0
        else:
            return -self.left[0]  # 奇数时左边多一个


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
    print("=== 题 1：第 K 大元素 ===")
    nums = [3, 2, 1, 5, 6, 4]
    k = 2
    print(f"输入: {nums}, k={k} → 第 {k} 大: {find_kth_largest(nums, k)}")

    print("\n=== 题 2：合并 K 个链表 ===")
    lists = [
        build_list([1, 4, 5]),
        build_list([1, 3, 4]),
        build_list([2, 6])
    ]
    print("输入:")
    for lst in lists:
        print(f"  {print_list(lst)}")
    merged = merge_k_lists(lists)
    print(f"输出: {print_list(merged)}")

    print("\n=== 题 3：数据流中位数 ===")
    mf = MedianFinder()
    mf.add_num(1)
    mf.add_num(2)
    print(f"add_num(1), add_num(2) → median = {mf.find_median()}")  # 1.5
    mf.add_num(3)
    print(f"add_num(3) → median = {mf.find_median()}")  # 2.0
