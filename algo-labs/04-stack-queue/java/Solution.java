import java.util.*;

/**
 * 专题 04：栈与队列
 * 包含三道经典题的实现：有效括号、最小栈、每日温度
 */
public class Solution {

    /**
     * 题 1：有效的括号
     * 时间 O(n)，空间 O(n)
     */
    public static boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        Map<Character, Character> map = new HashMap<>();
        map.put(')', '(');
        map.put(']', '[');
        map.put('}', '{');
        for (char c : s.toCharArray()) {
            if (map.containsKey(c)) {
                // 右括号：检查栈顶是否匹配
                if (stack.isEmpty() || !stack.peek().equals(map.get(c))) {
                    return false;
                }
                stack.pop();
            } else {
                // 左括号：压栈
                stack.push(c);
            }
        }
        return stack.isEmpty();
    }

    /**
     * 题 2：最小栈
     * 所有操作 O(1)
     */
    static class MinStack {
        private Deque<Integer> mainStack;
        private Deque<Integer> minStack;  // 辅助栈存当前最小值

        public MinStack() {
            mainStack = new ArrayDeque<>();
            minStack = new ArrayDeque<>();
        }

        public void push(int val) {
            mainStack.push(val);
            // 辅助栈压入 min(新元素, 当前最小)
            if (minStack.isEmpty()) {
                minStack.push(val);
            } else {
                minStack.push(Math.min(val, minStack.peek()));
            }
        }

        public void pop() {
            mainStack.pop();
            minStack.pop();
        }

        public int top() {
            return mainStack.peek();
        }

        public int getMin() {
            return minStack.peek();
        }
    }

    /**
     * 题 3：每日温度（单调栈）
     * 时间 O(n)，空间 O(n)
     */
    public static int[] dailyTemperatures(int[] temperatures) {
        int n = temperatures.length;
        int[] result = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();  // 存下标，对应温度递减

        for (int i = 0; i < n; i++) {
            // 当前温度 > 栈顶温度，说明栈顶找到了"下一个更高"
            while (!stack.isEmpty() && temperatures[i] > temperatures[stack.peek()]) {
                int prev = stack.pop();
                result[prev] = i - prev;  // 天数差
            }
            stack.push(i);
        }
        return result;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        System.out.println("=== 题 1：有效的括号 ===");
        System.out.println("输入: \"()\" → 输出: " + isValid("()"));
        System.out.println("输入: \"()[]{}\" → 输出: " + isValid("()[]{}"));
        System.out.println("输入: \"(]\" → 输出: " + isValid("(]"));
        System.out.println("输入: \"([)]\" → 输出: " + isValid("([)]"));

        System.out.println("\n=== 题 2：最小栈 ===");
        MinStack minStack = new MinStack();
        minStack.push(-2);
        minStack.push(0);
        minStack.push(-3);
        System.out.println("push(-2), push(0), push(-3)");
        System.out.println("getMin() → " + minStack.getMin());  // -3
        minStack.pop();
        System.out.println("pop()");
        System.out.println("top() → " + minStack.top());  // 0
        System.out.println("getMin() → " + minStack.getMin());  // -2

        System.out.println("\n=== 题 3：每日温度 ===");
        int[] temps = {73, 74, 75, 71, 69, 72, 76, 73};
        int[] days = dailyTemperatures(temps);
        System.out.println("输入: " + Arrays.toString(temps));
        System.out.println("输出: " + Arrays.toString(days));
    }
}
