import java.util.HashMap;
import java.util.Map;

/**
 * HashMap 底层原理深度解析
 * 
 * 核心机制：
 * 1. 哈希计算：(key.hashCode() ^ (key.hashCode() >>> 16)) & (capacity - 1)
 * 2. 冲突解决：链表 + 红黑树（JDK 8+）
 * 3. 扩容机制：容量翻倍，rehash 所有节点
 * 
 * 面试要点：
 * - 为什么容量是 2 的幂？→ 位运算代替取模，更快
 * - 为什么用红黑树？→ 链表长度 > 8 时，查找从 O(n) 优化到 O(log n)
 * - 为什么线程不安全？→ 并发扩容时可能形成环形链表（JDK 7）或数据丢失（JDK 8）
 */
public class HashMapDeepDive {

    public static void main(String[] args) {
        System.out.println("=== HashMap 底层原理演示 ===\n");

        // 演示 1：基本使用
        System.out.println("【演示 1】基本使用");
        Map<String, Integer> map = new HashMap<>();
        map.put("apple", 10);
        map.put("banana", 20);
        map.put("cherry", 30);
        System.out.println("插入 3 个元素: " + map);
        System.out.println("获取 apple: " + map.get("apple"));
        System.out.println("获取不存在的 key: " + map.get("grape"));  // null
        System.out.println();

        // 演示 2：哈希冲突
        System.out.println("【演示 2】哈希冲突（自定义 hashCode）");
        Map<Key, String> conflictMap = new HashMap<>();
        conflictMap.put(new Key("A", 1), "value1");
        conflictMap.put(new Key("B", 1), "value2");  // 相同 hash，冲突
        conflictMap.put(new Key("C", 1), "value3");  // 相同 hash，冲突
        System.out.println("插入 3 个相同 hash 的 key");
        System.out.println("获取 A: " + conflictMap.get(new Key("A", 1)));
        System.out.println("获取 B: " + conflictMap.get(new Key("B", 1)));
        System.out.println("冲突解决: 链表（JDK 8 后链表长度 > 8 转红黑树）");
        System.out.println();

        // 演示 3：扩容机制
        System.out.println("【演示 3】扩容机制");
        Map<String, Integer> resizeMap = new HashMap<>(4);  // 初始容量 4
        System.out.println("初始容量: 4, 负载因子: 0.75, 阈值: 3");
        
        resizeMap.put("a", 1);
        resizeMap.put("b", 2);
        resizeMap.put("c", 3);  // 第 3 个元素，触发扩容
        System.out.println("插入 3 个元素，触发扩容: 容量 4 → 8, 阈值 3 → 6");
        
        resizeMap.put("d", 4);
        resizeMap.put("e", 5);
        resizeMap.put("f", 6);
        resizeMap.put("g", 7);  // 第 7 个元素，再次扩容
        System.out.println("插入 7 个元素，再次扩容: 容量 8 → 16, 阈值 6 → 12");
        System.out.println("当前元素数: " + resizeMap.size());
        System.out.println();

        // 演示 4：线程不安全问题
        System.out.println("【演示 4】线程不安全问题（概念演示）");
        System.out.println("问题 1: 并发 put 导致数据丢失");
        System.out.println("  - 线程 A 读取 size=5，线程 B 读取 size=5");
        System.out.println("  - A 写入后 size=6，B 写入后 size=6（应该为 7）");
        System.out.println();
        System.out.println("问题 2: 并发扩容导致死循环（JDK 7）");
        System.out.println("  - 扩容时使用头插法，可能形成环形链表");
        System.out.println("  - JDK 8 改用尾插法，避免了死循环，但仍会数据丢失");
        System.out.println();
        System.out.println("解决方案: 使用 ConcurrentHashMap（见下一个示例）");
        System.out.println();

        // 演示 5：性能测试
        System.out.println("【演示 5】性能测试（插入 100 万元素）");
        Map<Integer, Integer> perfMap = new HashMap<>();
        int n = 1_000_000;
        
        long start = System.nanoTime();
        for (int i = 0; i < n; i++) {
            perfMap.put(i, i);
        }
        long insertTime = System.nanoTime() - start;
        
        start = System.nanoTime();
        for (int i = 0; i < n; i++) {
            perfMap.get(i);
        }
        long getTime = System.nanoTime() - start;
        
        System.out.printf("插入 %d 个元素: %.2f ms%n", n, insertTime / 1_000_000.0);
        System.out.printf("查询 %d 次: %.2f ms%n", n, getTime / 1_000_000.0);
        System.out.printf("平均每次查询: %.0f ns%n", (double) getTime / n);
    }

    /**
     * 自定义 Key 类，用于演示哈希冲突
     */
    static class Key {
        private String name;
        private int hash;

        public Key(String name, int hash) {
            this.name = name;
            this.hash = hash;
        }

        @Override
        public int hashCode() {
            return hash;  // 强制返回相同 hash，制造冲突
        }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof Key)) return false;
            Key other = (Key) obj;
            return name.equals(other.name);
        }

        @Override
        public String toString() {
            return name;
        }
    }
}
