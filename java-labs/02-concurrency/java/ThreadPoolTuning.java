import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 线程池参数调优与工作流程演示
 *
 * 核心参数（ThreadPoolExecutor 构造函数）：
 * 1. corePoolSize: 核心线程数（即使空闲也保留）
 * 2. maximumPoolSize: 最大线程数（队列满时创建）
 * 3. keepAliveTime: 非核心线程空闲存活时间
 * 4. workQueue: 任务队列（ArrayBlockingQueue、LinkedBlockingQueue、SynchronousQueue）
 * 5. handler: 拒绝策略（AbortPolicy、CallerRunsPolicy、DiscardPolicy、DiscardOldestPolicy）
 *
 * 工作流程（execute 方法）：
 * 1. 当前线程数 < corePoolSize → 创建核心线程执行任务
 * 2. 当前线程数 >= corePoolSize → 任务放入队列
 * 3. 队列满且线程数 < maximumPoolSize → 创建非核心线程执行任务
 * 4. 队列满且线程数 = maximumPoolSize → 执行拒绝策略
 *
 * 面试重点：
 * - 如何设置线程池大小（CPU 密集型 vs IO 密集型）
 * - 不同队列的选择场景
 * - 拒绝策略的适用场景
 */
public class ThreadPoolTuning {
    
    public static void main(String[] args) throws Exception {
        System.out.println("=== 线程池参数详解 ===\n");
        
        // ========== 参数设置原则 ==========
        int cpuCores = Runtime.getRuntime().availableProcessors();
        System.out.println("CPU 核心数: " + cpuCores);
        System.out.println();
        
        System.out.println("【CPU 密集型任务】");
        System.out.println("  特点：大量计算，很少 IO 等待");
        System.out.println("  线程数：N + 1（N = CPU 核心数）");
        System.out.println("  原因：减少上下文切换，+1 防止偶缺页中断");
        System.out.println("  示例：加密、压缩、复杂算法");
        System.out.println();
        
        System.out.println("【IO 密集型任务】");
        System.out.println("  特点：大量 IO 等待（网络、磁盘）");
        System.out.println("  线程数：2N ~ N * (1 + W/C)");
        System.out.println("  公式：W = 等待时间，C = 计算时间");
        System.out.println("  示例：HTTP 请求、数据库查询、文件读写");
        System.out.println();
        
        // ========== 演示 1：核心线程 vs 最大线程 ==========
        System.out.println("=== 演示 1：核心线程与最大线程 ===");
        ThreadPoolExecutor pool1 = new ThreadPoolExecutor(
            2,              // corePoolSize
            4,              // maximumPoolSize
            60L,            // keepAliveTime
            TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(2),  // 队列容量 2
            new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略：调用者执行
        );
        
        System.out.println("配置：core=2, max=4, queue=2");
        System.out.println("提交 6 个任务（每个耗时 2 秒）：");
        
        AtomicInteger taskCounter = new AtomicInteger(0);
        for (int i = 0; i < 6; i++) {
            final int taskId = i;
            pool1.execute(() -> {
                int count = taskCounter.incrementAndGet();
                System.out.println("任务 " + taskId + " 开始执行（第 " + count + " 个并发）- " 
                    + Thread.currentThread().getName());
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println("任务 " + taskId + " 完成");
            });
        }
        
        pool1.shutdown();
        pool1.awaitTermination(10, TimeUnit.SECONDS);
        System.out.println();
        
        // ========== 演示 2：不同队列的影响 ==========
        System.out.println("=== 演示 2：不同队列类型 ===");
        
        System.out.println("【ArrayBlockingQueue（有界队列）】");
        System.out.println("  特点：固定容量，必须指定大小");
        System.out.println("  场景：内存有限，需要控制任务堆积");
        System.out.println("  风险：队列满时触发拒绝策略");
        System.out.println();
        
        System.out.println("【LinkedBlockingQueue（无界队列）】");
        System.out.println("  特点：默认 Integer.MAX_VALUE，近似无界");
        System.out.println("  场景：任务量不确定，允许排队");
        System.out.println("  风险：OOM（任务堆积过多）");
        System.out.println("  注意：maximumPoolSize 无效（队列不会满）");
        System.out.println();
        
        System.out.println("【SynchronousQueue（同步队列）】");
        System.out.println("  特点：容量为 0，每个 put 必须等待 take");
        System.out.println("  场景：希望任务立即被执行，不排队");
        System.out.println("  典型：Executors.newCachedThreadPool()");
        System.out.println();
        
        // ========== 演示 3：拒绝策略 ==========
        System.out.println("=== 演示 3：四种拒绝策略 ===");
        
        ThreadPoolExecutor[] pools = new ThreadPoolExecutor[4];
        String[] policyNames = {
            "AbortPolicy（抛出异常）",
            "CallerRunsPolicy（调用者执行）",
            "DiscardPolicy（丢弃任务）",
            "DiscardOldestPolicy（丢弃最老任务）"
        };
        RejectedExecutionHandler[] handlers = {
            new ThreadPoolExecutor.AbortPolicy(),
            new ThreadPoolExecutor.CallerRunsPolicy(),
            new ThreadPoolExecutor.DiscardPolicy(),
            new ThreadPoolExecutor.DiscardOldestPolicy()
        };
        
        for (int i = 0; i < 4; i++) {
            pools[i] = new ThreadPoolExecutor(
                1, 1, 0L, TimeUnit.SECONDS,
                new ArrayBlockingQueue<>(1),
                handlers[i]
            );
        }
        
        for (int i = 0; i < 4; i++) {
            System.out.println("【" + policyNames[i] + "】");
            try {
                // 提交 3 个任务（core=1, queue=1，第 3 个会触发拒绝）
                for (int j = 0; j < 3; j++) {
                    final int taskId = j;
                    pools[i].execute(() -> {
                        try {
                            Thread.sleep(1000);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    });
                }
                System.out.println("  3 个任务全部提交成功");
            } catch (RejectedExecutionException e) {
                System.out.println("  第 3 个任务被拒绝，抛出异常");
            }
            pools[i].shutdownNow();
            System.out.println();
        }
        
        // ========== 演示 4：自定义线程池配置 ==========
        System.out.println("=== 演示 4：生产环境推荐配置 ===");
        
        // IO 密集型任务（如 HTTP 请求）
        ThreadPoolExecutor ioPool = new ThreadPoolExecutor(
            cpuCores * 2,                    // 核心线程数
            cpuCores * 4,                    // 最大线程数
            60L, TimeUnit.SECONDS,           // 非核心线程空闲 60 秒回收
            new LinkedBlockingQueue<>(1000), // 有界队列，防止 OOM
            new ThreadFactory() {            // 自定义线程工厂（便于排查问题）
                private final AtomicInteger counter = new AtomicInteger(0);
                @Override
                public Thread newThread(Runnable r) {
                    Thread t = new Thread(r);
                    t.setName("IO-Worker-" + counter.incrementAndGet());
                    t.setDaemon(false);  // 非守护线程
                    return t;
                }
            },
            new ThreadPoolExecutor.CallerRunsPolicy()  // 队列满时由调用者执行（降级策略）
        );
        
        System.out.println("IO 密集型线程池配置：");
        System.out.println("  核心线程：" + ioPool.getCorePoolSize());
        System.out.println("  最大线程：" + ioPool.getMaximumPoolSize());
        System.out.println("  队列容量：1000");
        System.out.println("  拒绝策略：CallerRunsPolicy（降级保护）");
        
        ioPool.shutdown();
        
        System.out.println("\n=== 监控建议 ===");
        System.out.println("1. 定期获取：poolSize、activeCount、queue.size()");
        System.out.println("2. 告警指标：队列堆积率、拒绝次数、任务平均耗时");
        System.out.println("3. 动态调参：通过 JMX 或配置中心实时调整参数");
    }
}
