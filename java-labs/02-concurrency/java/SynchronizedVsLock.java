import java.util.concurrent.locks.ReentrantLock;

/**
 * synchronized vs ReentrantLock 对比演示
 *
 * 核心区别：
 * 1. synchronized: JVM 层面实现，自动释放锁，不可中断
 * 2. ReentrantLock: API 层面实现，手动释放锁，支持中断、超时、公平锁
 *
 * 性能对比（JDK 6 之后）：
 * - synchronized 经过优化（偏向锁、轻量级锁），性能接近 ReentrantLock
 * - 高竞争场景 ReentrantLock 略优（支持公平锁、条件变量）
 *
 * 面试重点：
 * - synchronized 锁升级过程
 * - ReentrantLock 的 AQS 原理
 * - 什么场景选择哪种锁
 */
public class SynchronizedVsLock {
    
    private int counter = 0;
    private final Object syncLock = new Object();
    private final ReentrantLock reentrantLock = new ReentrantLock();
    
    // ========== synchronized 方式 ==========
    public void incrementSync() {
        synchronized (syncLock) {
            counter++;
        }
    }
    
    // ========== ReentrantLock 方式 ==========
    public void incrementLock() {
        reentrantLock.lock();
        try {
            counter++;
        } finally {
            reentrantLock.unlock();  // 必须在 finally 中释放
        }
    }
    
    // ========== 可中断锁（ReentrantLock 独有）==========
    public void interruptibleLock() throws InterruptedException {
        // lockInterruptibly() 允许线程在等待锁时被中断
        reentrantLock.lockInterruptibly();
        try {
            System.out.println(Thread.currentThread().getName() + " 获取到锁");
            Thread.sleep(2000);  // 模拟长时间持有
        } finally {
            reentrantLock.unlock();
        }
    }
    
    // ========== 尝试获取锁（ReentrantLock 独有）==========
    public boolean tryLockDemo() {
        // tryLock() 非阻塞尝试，立即返回
        if (reentrantLock.tryLock()) {
            try {
                System.out.println(Thread.currentThread().getName() + " 成功获取锁");
                return true;
            } finally {
                reentrantLock.unlock();
            }
        } else {
            System.out.println(Thread.currentThread().getName() + " 获取锁失败");
            return false;
        }
    }
    
    public static void main(String[] args) throws Exception {
        SynchronizedVsLock demo = new SynchronizedVsLock();
        
        System.out.println("=== 性能对比测试 ===");
        int iterations = 1_000_000;
        int threads = 4;
        
        // 测试 synchronized
        demo.counter = 0;
        long start = System.currentTimeMillis();
        Thread[] syncThreads = new Thread[threads];
        for (int i = 0; i < threads; i++) {
            syncThreads[i] = new Thread(() -> {
                for (int j = 0; j < iterations / threads; j++) {
                    demo.incrementSync();
                }
            });
            syncThreads[i].start();
        }
        for (Thread t : syncThreads) t.join();
        long syncTime = System.currentTimeMillis() - start;
        
        // 测试 ReentrantLock
        demo.counter = 0;
        start = System.currentTimeMillis();
        Thread[] lockThreads = new Thread[threads];
        for (int i = 0; i < threads; i++) {
            lockThreads[i] = new Thread(() -> {
                for (int j = 0; j < iterations / threads; j++) {
                    demo.incrementLock();
                }
            });
            lockThreads[i].start();
        }
        for (Thread t : lockThreads) t.join();
        long lockTime = System.currentTimeMillis() - start;
        
        System.out.println("synchronized: " + syncTime + "ms");
        System.out.println("ReentrantLock: " + lockTime + "ms");
        System.out.println();
        
        // ========== 可中断锁演示 ==========
        System.out.println("=== 可中断锁演示 ===");
        Thread t1 = new Thread(() -> {
            try {
                demo.interruptibleLock();
            } catch (InterruptedException e) {
                System.out.println(Thread.currentThread().getName() + " 被中断");
            }
        }, "Thread-1");
        
        Thread t2 = new Thread(() -> {
            try {
                Thread.sleep(500);  // 等 t1 先获取锁
                demo.interruptibleLock();
            } catch (InterruptedException e) {
                System.out.println(Thread.currentThread().getName() + " 被中断");
            }
        }, "Thread-2");
        
        t1.start();
        t2.start();
        Thread.sleep(1000);  // 等 t2 开始等待锁
        t2.interrupt();      // 中断 t2
        t1.join();
        t2.join();
        System.out.println();
        
        // ========== tryLock 演示 ==========
        System.out.println("=== tryLock 演示 ===");
        Thread t3 = new Thread(demo::tryLockDemo, "Thread-3");
        Thread t4 = new Thread(demo::tryLockDemo, "Thread-4");
        t3.start();
        Thread.sleep(100);  // 让 t3 先获取锁
        t4.start();
        t3.join();
        t4.join();
        
        System.out.println("\n=== 选择建议 ===");
        System.out.println("1. 简单同步场景 → synchronized（代码简洁，JVM 优化好）");
        System.out.println("2. 需要中断/超时/公平锁 → ReentrantLock");
        System.out.println("3. 读写分离场景 → ReentrantReadWriteLock");
        System.out.println("4. 高竞争场景 → ReentrantLock（支持公平锁避免饥饿）");
    }
}
