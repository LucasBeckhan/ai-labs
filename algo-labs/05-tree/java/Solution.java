import java.util.*;

/**
 * 专题 05：二叉树
 * 包含经典题的实现：四种遍历、最大深度、翻转二叉树
 */

// 二叉树节点定义
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;
    TreeNode(int val) { this.val = val; }
}

public class Solution {

    /**
     * 题 1a：前序遍历（递归）- 根左右
     */
    public static List<Integer> preorderTraversal(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        preorder(root, result);
        return result;
    }
    private static void preorder(TreeNode node, List<Integer> result) {
        if (node == null) return;
        result.add(node.val);      // 根
        preorder(node.left, result);   // 左
        preorder(node.right, result);  // 右
    }

    /**
     * 题 1b：中序遍历（递归）- 左根右
     */
    public static List<Integer> inorderTraversal(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        inorder(root, result);
        return result;
    }
    private static void inorder(TreeNode node, List<Integer> result) {
        if (node == null) return;
        inorder(node.left, result);    // 左
        result.add(node.val);      // 根
        inorder(node.right, result);   // 右
    }

    /**
     * 题 1c：后序遍历（递归）- 左右根
     */
    public static List<Integer> postorderTraversal(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        postorder(root, result);
        return result;
    }
    private static void postorder(TreeNode node, List<Integer> result) {
        if (node == null) return;
        postorder(node.left, result);  // 左
        postorder(node.right, result); // 右
        result.add(node.val);      // 根
    }

    /**
     * 题 1d：层序遍历（BFS）
     */
    public static List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;
        
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        
        while (!queue.isEmpty()) {
            int size = queue.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            result.add(level);
        }
        return result;
    }

    /**
     * 题 2：二叉树的最大深度
     * 时间 O(n)，空间 O(h)
     */
    public static int maxDepth(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
    }

    /**
     * 题 3：翻转二叉树
     * 时间 O(n)，空间 O(h)
     */
    public static TreeNode invertTree(TreeNode root) {
        if (root == null) return null;
        // 交换左右子树
        TreeNode temp = root.left;
        root.left = root.right;
        root.right = temp;
        // 递归翻转子树
        invertTree(root.left);
        invertTree(root.right);
        return root;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        // 构造测试树：
        //     1
        //    / \
        //   2   3
        //  / \
        // 4   5
        TreeNode root = new TreeNode(1);
        root.left = new TreeNode(2);
        root.right = new TreeNode(3);
        root.left.left = new TreeNode(4);
        root.left.right = new TreeNode(5);

        System.out.println("=== 题 1：二叉树遍历 ===");
        System.out.println("前序（根左右）: " + preorderTraversal(root));
        System.out.println("中序（左根右）: " + inorderTraversal(root));
        System.out.println("后序（左右根）: " + postorderTraversal(root));
        System.out.println("层序: " + levelOrder(root));

        System.out.println("\n=== 题 2：最大深度 ===");
        System.out.println("深度: " + maxDepth(root));  // 3

        System.out.println("\n=== 题 3：翻转二叉树 ===");
        TreeNode inverted = invertTree(root);
        System.out.println("翻转后层序: " + levelOrder(inverted));
        // 原来: [[1], [2, 3], [4, 5]]
        // 翻转后: [[1], [3, 2], [5, 4]]
    }
}
