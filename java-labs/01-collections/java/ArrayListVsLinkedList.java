import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

/**
 * ArrayList vs LinkedList 性能对比
 * 
 * 核心结论：
 * - 随机访问：ArrayList O(1) vs LinkedList O(n)
 * - 头部插入：ArrayList O(n) vs LinkedList O(1)
 * - 尾部插入：两者都是 O(1)（均摊）
 * 
 * 面试要点：
 * - ArrayList 基于数组，内存连续，CPU 缓存友好
 * - LinkedList 基于双向链表，每个节点有额外指针开销
 * - 现代 CPU 架构下，ArrayList 几乎总是更快（即使头部插入）
 */
public class ArrayListVsLinkedList {

    public static void main(String[] args) {
        int n = 100_000;
        
        System.out.println("=== ArrayList vs LinkedList 性能对比 ===");
        System.out.println("数据规模: " + n + " 个元素\n");

        // 测试 1：尾部插入
        System.out.println("【测试 1】尾部插入 " + n + " 个元素");
        List<Integer> arrayList = new ArrayList<>();
        List<Integer> linkedList = new LinkedList<>();
        
        long start = System.nanoTime();
        for (int i = 0; i < n; i++) {
            arrayList.add(i);
        }
        long arrayTime = System.nanoTime() - start;
        
        start = System.nanoTime();
        for (int i = 0; i < n; i++) {
            linkedList.add(i);
        }
        long linkedTime = System.nanoTime() - start;
        
        System.out.printf("ArrayList:  %.2f ms%n", arrayTime / 1_000_000.0);
        System.out.printf("LinkedList: %.2f ms%n", linkedTime / 1_000_000.0);
        System.out.printf("差异: %.2fx%n%n", (double) linkedTime / arrayTime);

        // 测试 2：随机访问
        System.out.println("【测试 2】随机访问 10000 次");
        int accessCount = 10000;
        
        start = System.nanoTime();
        for (int i = 0; i < accessCount; i++) {
            int index = (int) (Math.random() * n);
            arrayList.get(index);
        }
        arrayTime = System.nanoTime() - start;
        
        start = System.nanoTime();
        for (int i = 0; i < accessCount; i++) {
            int index = (int) (Math.random() * n);
            linkedList.get(index);
        }
        linkedTime = System.nanoTime() - start;
        
        System.out.printf("ArrayList:  %.2f ms%n", arrayTime / 1_000_000.0);
        System.out.printf("LinkedList: %.2f ms%n", linkedTime / 1_000_000.0);
        System.out.printf("差异: %.2fx%n%n", (double) linkedTime / arrayTime);

        // 测试 3：头部插入
        System.out.println("【测试 3】头部插入 " + n + " 个元素");
        arrayList = new ArrayList<>();
        linkedList = new LinkedList<>();
        
        start = System.nanoTime();
        for (int i = 0; i < n; i++) {
            arrayList.add(0, i);
        }
        arrayTime = System.nanoTime() - start;
        
        start = System.nanoTime();
        for (int i = 0; i < n; i++) {
            linkedList.add(0, i);
        }
        linkedTime = System.nanoTime() - start;
        
        System.out.printf("ArrayList:  %.2f ms%n", arrayTime / 1_000_000.0);
        System.out.printf("LinkedList: %.2f ms%n", linkedTime / 1_000_000.0);
        System.out.printf("差异: %.2fx%n%n", (double) arrayTime / linkedTime);

        // 内存占用对比
        System.out.println("【内存占用】");
        System.out.println("ArrayList: 数组 + 少量元数据");
        System.out.println("LinkedList: 每个节点 = 值 + prev指针 + next指针 = 24字节（64位JVM）");
        System.out.println("结论: LinkedList 内存开销约 3x ArrayList");
    }
}
