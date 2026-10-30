import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * ConcurrentHashMap 线程安全机制演示
 * 
 * 核心机制（JDK 8）：
 * 1. CAS + synchronized：锁粒度从段（JDK 7）降到桶（JDK 8）
 * 2. size() 实现：baseCount + CounterCell[]（类似 LongAdder）
 * 3. 扩容机制：多线程协助迁移（transfer）
 * 
 * 面试要点：
 * - 为什么不用 HashTable？→ HashTable 全表锁，并发度只有 1
 * - size() 如何保证准确？→ baseCount + CounterCell[]，失败时重试
 * - get 为什么不用加锁？→ 读操作通过 volatile 保证可见性
 */
public class ConcurrentHashMapDemo {

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== ConcurrentHashMap 线程安全演示 ===\n");

        // 演示 1：线程安全问题（HashMap）
        System.out.println("【演示 1】HashMap 并发写入导致数据丢失");
        Map<Integer, Integer> unsafeMap = new HashMap<>();
        int threadCount = 10;
        int elementsPerThread = 1000;
        CountDownLatch latch1 = new CountDownLatch(threadCount);
        ExecutorService executor1 = Executors.newFixedThreadPool(threadCount);

        for (int i = 0; i < threadCount; i++) {
            final int threadId = i;
            executor1.submit(() -> {
                for (int j = 0; j < elementsPerThread; j++) {
                    int key = threadId * elementsPerThread + j;
                    unsafeMap.put(key, key);
                }
                latch1.countDown();
            });
        }

        latch1.await();
        executor1.shutdown();
        int expectedSize = threadCount * elementsPerThread;
        System.out.println("预期元素数: " + expectedSize);
        System.out.println("实际元素数: " + unsafeMap.size());
        System.out.println("丢失元素: " + (expectedSize - unsafeMap.size()));
        System.out.println();

        // 演示 2：线程安全（ConcurrentHashMap）
        System.out.println("【演示 2】ConcurrentHashMap 并发写入数据完整");
        Map<Integer, Integer> safeMap = new ConcurrentHashMap<>();
        CountDownLatch latch2 = new CountDownLatch(threadCount);
        ExecutorService executor2 = Executors.newFixedThreadPool(threadCount);

        for (int i = 0; i < threadCount; i++) {
            final int threadId = i;
            executor2.submit(() -> {
                for (int j = 0; j < elementsPerThread; j++) {
                    int key = threadId * elementsPerThread + j;
                    safeMap.put(key, key);
                }
                latch2.countDown();
            });
        }

        latch2.await();
        executor2.shutdown();
        System.out.println("预期元素数: " + expectedSize);
        System.out.println("实际元素数: " + safeMap.size());
        System.out.println("丢失元素: " + (expectedSize - safeMap.size()));
        System.out.println();

        // 演示 3：性能对比
        System.out.println("【演示 3】性能对比（10 线程并发写入 10 万元素）");
        int perfThreads = 10;
        int perfElements = 100_000;
        
        // HashMap（不安全，仅做对比）
        Map<Integer, Integer> perfUnsafe = new HashMap<>();
        CountDownLatch latch3 = new CountDownLatch(perfThreads);
        ExecutorService executor3 = Executors.newFixedThreadPool(perfThreads);
        
        long start = System.nanoTime();
        for (int i = 0; i < perfThreads; i++) {
            final int threadId = i;
            executor3.submit(() -> {
                for (int j = 0; j < perfElements / perfThreads; j++) {
                    int key = threadId * (perfElements / perfThreads) + j;
                    perfUnsafe.put(key, key);
                }
                latch3.countDown();
            });
        }
        latch3.await();
        long unsafeTime = System.nanoTime() - start;
        executor3.shutdown();

        // ConcurrentHashMap（安全）
        Map<Integer, Integer> perfSafe = new ConcurrentHashMap<>();
        CountDownLatch latch4 = new CountDownLatch(perfThreads);
        ExecutorService executor4 = Executors.newFixedThreadPool(perfThreads);
        
        start = System.nanoTime();
        for (int i = 0; i < perfThreads; i++) {
            final int threadId = i;
            executor4.submit(() -> {
                for (int j = 0; j < perfElements / perfThreads; j++) {
                    int key = threadId * (perfElements / perfThreads) + j;
                    perfSafe.put(key, key);
                }
                latch4.countDown();
            });
        }
        latch4.await();
        long safeTime = System.nanoTime() - start;
        executor4.shutdown();

        System.out.printf("HashMap (不安全):        %.2f ms, 实际元素: %d%n", 
            unsafeTime / 1_000_000.0, perfUnsafe.size());
        System.out.printf("ConcurrentHashMap (安全): %.2f ms, 实际元素: %d%n", 
            safeTime / 1_000_000.0, perfSafe.size());
        System.out.printf("性能差异: ConcurrentHashMap 慢 %.2fx%n", 
            (double) safeTime / unsafeTime);
        System.out.println();

        // 演示 4：size() 方法原理
        System.out.println("【演示 4】ConcurrentHashMap.size() 实现原理");
        System.out.println("JDK 8 实现:");
        System.out.println("  1. 维护 baseCount（无竞争时直接 CAS 更新）");
        System.out.println("  2. 竞争激烈时，使用 CounterCell[]（类似 LongAdder 的分段计数）");
        System.out.println("  3. size() = baseCount + sum(CounterCell[])");
        System.out.println("  4. 优势：减少竞争，提高并发性能");
        System.out.println();

        // 演示 5：常用方法
        System.out.println("【演示 5】ConcurrentHashMap 特有方法");
        ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
        
        // putIfAbsent：如果 key 不存在则插入
        map.putIfAbsent("apple", 10);
        map.putIfAbsent("apple", 20);  // 不会覆盖
        System.out.println("putIfAbsent('apple', 10) then putIfAbsent('apple', 20)");
        System.out.println("结果: " + map.get("apple"));  // 10
        
        // computeIfAbsent：如果 key 不存在则计算并插入
        map.computeIfAbsent("banana", k -> 100);
        System.out.println("computeIfAbsent('banana', k -> 100)");
        System.out.println("结果: " + map.get("banana"));  // 100
        
        // compute：原子性地更新值
        map.compute("apple", (k, v) -> v == null ? 1 : v + 1);
        System.out.println("compute('apple', (k, v) -> v + 1)");
        System.out.println("结果: " + map.get("apple"));  // 11
    }
}
