"""
专题 05：二叉树
包含经典题的实现：四种遍历、最大深度、翻转二叉树
"""
from collections import deque


class TreeNode:
    """二叉树节点定义"""
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def preorder_traversal(root: TreeNode) -> list[int]:
    """题 1a：前序遍历（递归）- 根左右"""
    result = []
    def preorder(node):
        if not node:
            return
        result.append(node.val)      # 根
        preorder(node.left)          # 左
        preorder(node.right)         # 右
    preorder(root)
    return result


def inorder_traversal(root: TreeNode) -> list[int]:
    """题 1b：中序遍历（递归）- 左根右"""
    result = []
    def inorder(node):
        if not node:
            return
        inorder(node.left)           # 左
        result.append(node.val)      # 根
        inorder(node.right)          # 右
    inorder(root)
    return result


def postorder_traversal(root: TreeNode) -> list[int]:
    """题 1c：后序遍历（递归）- 左右根"""
    result = []
    def postorder(node):
        if not node:
            return
        postorder(node.left)         # 左
        postorder(node.right)        # 右
        result.append(node.val)      # 根
    postorder(root)
    return result


def level_order(root: TreeNode) -> list[list[int]]:
    """题 1d：层序遍历（BFS）"""
    if not root:
        return []
    result = []
    queue = deque([root])
    
    while queue:
        level_size = len(queue)
        level = []
        for _ in range(level_size):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result


def max_depth(root: TreeNode) -> int:
    """
    题 2：二叉树的最大深度
    时间 O(n)，空间 O(h)
    """
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))


def invert_tree(root: TreeNode) -> TreeNode:
    """
    题 3：翻转二叉树
    时间 O(n)，空间 O(h)
    """
    if not root:
        return None
    # 交换左右子树
    root.left, root.right = root.right, root.left
    # 递归翻转子树
    invert_tree(root.left)
    invert_tree(root.right)
    return root


# ========== 测试 ==========
if __name__ == "__main__":
    # 构造测试树：
    #     1
    #    / \
    #   2   3
    #  / \
    # 4   5
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.left.right = TreeNode(5)

    print("=== 题 1：二叉树遍历 ===")
    print(f"前序（根左右）: {preorder_traversal(root)}")
    print(f"中序（左根右）: {inorder_traversal(root)}")
    print(f"后序（左右根）: {postorder_traversal(root)}")
    print(f"层序: {level_order(root)}")

    print("\n=== 题 2：最大深度 ===")
    print(f"深度: {max_depth(root)}")  # 3

    print("\n=== 题 3：翻转二叉树 ===")
    inverted = invert_tree(root)
    print(f"翻转后层序: {level_order(inverted)}")
    # 原来: [[1], [2, 3], [4, 5]]
    # 翻转后: [[1], [3, 2], [5, 4]]
