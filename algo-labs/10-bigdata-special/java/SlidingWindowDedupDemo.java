import java.util.*;

/**
 * 滑动窗口去重
 * 用途：流式数据中只保留最近 N 个元素内的去重
 * 特点：插入 O(1)，查询 O(1)，空间 O(N)
 */
public class SlidingWindowDedupDemo {
    private Queue<String> window;      // 队列维护窗口内的元素顺序
    private Set<String> seen;          // HashSet 快速判断重复
    private int maxSize;               // 窗口最大容量

    public SlidingWindowDedupDemo(int maxSize) {
        this.maxSize = maxSize;
        this.window = new LinkedList<>();
        this.seen = new HashSet<>();
    }

    /**
     * 尝试添加元素（如果窗口内已存在则拒绝）
     * @return true = 添加成功，false = 重复被拒绝
     */
    public boolean add(String element) {
        if (seen.contains(element)) {
            return false;  // 窗口内已存在，拒绝
        }

        // 窗口满了，移除最老的元素
        if (window.size() >= maxSize) {
            String oldest = window.poll();
            seen.remove(oldest);
        }

        // 添加新元素
        window.offer(element);
        seen.add(element);
        return true;
    }

    /**
     * 查询元素是否在窗口内
     */
    public boolean contains(String element) {
        return seen.contains(element);
    }

    /**
     * 获取当前窗口大小
     */
    public int size() {
        return window.size();
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        SlidingWindowDedupDemo dedup = new SlidingWindowDedupDemo(5);

        System.out.println("=== 滑动窗口去重（窗口大小 5）===");
        String[] stream = {"A", "B", "C", "A", "D", "E", "B", "F"};
        
        for (String item : stream) {
            boolean added = dedup.add(item);
            System.out.printf("添加 '%s' → %s, 窗口: %s%n",
                item, added ? "成功" : "重复", dedup.window);
        }

        System.out.println("\n最终窗口内容: " + dedup.window);
        System.out.printf("查询 'A' 是否在窗口内 → %s%n", dedup.contains("A"));
        System.out.printf("查询 'B' 是否在窗口内 → %s%n", dedup.contains("B"));
    }
}
