import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

/**
 * 死锁检测与避免演示
 *
 * 死锁四条件（Coffman 条件）：
 * 1. 互斥（Mutual Exclusion）：资源只能被一个线程持有
 * 2. 占有等待（Hold and Wait）：持有资源并等待其他资源
 * 3. 不可剥夺（No Preemption）：资源只能由持有者释放
 * 4. 循环等待（Circular Wait）：存在环形等待链
 *
 * 避免策略：
 * 1. 破坏循环等待：锁排序（所有线程按相同顺序获取锁）
 * 2. 破坏占有等待：一次性获取所有锁
 * 3. 使用 tryLock 超时放弃
 * 4. 定期检测死锁并恢复
 *
 * 面试重点：
 * - 手写死锁代码
 * - 死锁检测方法（jstack、ThreadMXBean）
 * - 生产环境如何避免死锁
 */
public class DeadlockDetection {
    
    private static final Object lock1 = new Object();
    private static final Object lock2 = new Object();
    
    // ========== 经典死锁场景 ==========
    public static void createDeadlock() {
        Thread t1 = new Thread(() -> {
            synchronized (lock1) {
                System.out.println("Thread-1: 持有 lock1，等待 lock2...");
                try { Thread.sleep(100); } catch (InterruptedException e) {}
                synchronized (lock2) {
                    System.out.println("Thread-1: 获取 lock2 成功（不会执行到这里）");
                }
            }
        }, "Deadlock-Thread-1");
        
        Thread t2 = new Thread(() -> {
            synchronized (lock2) {
                System.out.println("Thread-2: 持有 lock2，等待 lock1...");
                try { Thread.sleep(100); } catch (InterruptedException e) {}
                synchronized (lock1) {
                    System.out.println("Thread-2: 获取 lock1 成功（不会执行到这里）");
                }
            }
        }, "Deadlock-Thread-2");
        
        t1.start();
        t2.start();
        
        System.out.println("死锁已创建，两个线程互相等待...");
        System.out.println("可以使用 jstack 检测：jstack <pid>");
        
        // 等待 2 秒后强制退出（避免程序卡死）
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.exit(0);
    }
    
    // ========== 使用 ThreadMXBean 检测死锁 ==========
    public static boolean detectDeadlock() {
        ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
        long[] deadlockedThreads = threadMXBean.findDeadlockedThreads();
        
        if (deadlockedThreads != null) {
            System.out.println("检测到死锁！");
            ThreadInfo[] threadInfos = threadMXBean.getThreadInfo(deadlockedThreads, true, true);
            for (ThreadInfo threadInfo : threadInfos) {
                System.out.println("线程：" + threadInfo.getThreadName());
                System.out.println("  等待锁：" + threadInfo.getLockName());
                System.out.println("  被持有者：" + threadInfo.getLockOwnerName());
            }
            return true;
        }
        return false;
    }
    
    // ========== 避免策略 1：锁排序 ==========
    public static void lockOrdering() {
        System.out.println("\n=== 避免策略 1：锁排序 ===");
        System.out.println("原则：所有线程按相同顺序获取锁（如按锁的 hashCode 排序）");
        
        Thread t1 = new Thread(() -> {
            synchronized (lock1) {  // 先获取 lock1
                System.out.println("Thread-1: 获取 lock1");
                try { Thread.sleep(100); } catch (InterruptedException e) {}
                synchronized (lock2) {  // 再获取 lock2
                    System.out.println("Thread-1: 获取 lock2，执行成功");
                }
            }
        });
        
        Thread t2 = new Thread(() -> {
            synchronized (lock1) {  // 同样先获取 lock1（而不是 lock2）
                System.out.println("Thread-2: 获取 lock1");
                try { Thread.sleep(100); } catch (InterruptedException e) {}
                synchronized (lock2) {  // 再获取 lock2
                    System.out.println("Thread-2: 获取 lock2，执行成功");
                }
            }
        });
        
        t1.start();
        t2.start();
        
        try {
            t1.join();
            t2.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        
        System.out.println("✓ 没有死锁，两个线程都执行成功");
    }
    
    // ========== 避免策略 2：tryLock 超时放弃 ==========
    public static void tryLockTimeout() {
        System.out.println("\n=== 避免策略 2：tryLock 超时放弃 ===");
        
        ReentrantLock rLock1 = new ReentrantLock();
        ReentrantLock rLock2 = new ReentrantLock();
        
        Thread t1 = new Thread(() -> {
            try {
                if (rLock1.tryLock(1, TimeUnit.SECONDS)) {
                    System.out.println("Thread-1: 获取 rLock1");
                    Thread.sleep(100);
                    if (rLock2.tryLock(1, TimeUnit.SECONDS)) {
                        System.out.println("Thread-1: 获取 rLock2，执行成功");
                        rLock2.unlock();
                    } else {
                        System.out.println("Thread-1: 获取 rLock2 超时，放弃");
                    }
                    rLock1.unlock();
                }
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        });
        
        Thread t2 = new Thread(() -> {
            try {
                if (rLock2.tryLock(1, TimeUnit.SECONDS)) {
                    System.out.println("Thread-2: 获取 rLock2");
                    Thread.sleep(100);
                    if (rLock1.tryLock(1, TimeUnit.SECONDS)) {
                        System.out.println("Thread-2: 获取 rLock1，执行成功");
                        rLock1.unlock();
                    } else {
                        System.out.println("Thread-2: 获取 rLock1 超时，放弃");
                    }
                    rLock2.unlock();
                }
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        });
        
        t1.start();
        t2.start();
        
        try {
            t1.join();
            t2.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        
        System.out.println("✓ 使用 tryLock 超时放弃，避免死锁");
    }
    
    // ========== 避免策略 3：一次性获取所有锁 ==========
    public static void acquireAllLocks() {
        System.out.println("\n=== 避免策略 3：一次性获取所有锁 ===");
        
        Thread t1 = new Thread(() -> {
            synchronized (lock1) {
                synchronized (lock2) {
                    System.out.println("Thread-1: 一次性获取 lock1 和 lock2");
                    // 执行业务逻辑
                }
            }
        });
        
        Thread t2 = new Thread(() -> {
            synchronized (lock1) {  // 同样的顺序
                synchronized (lock2) {
                    System.out.println("Thread-2: 一次性获取 lock1 和 lock2");
                    // 执行业务逻辑
                }
            }
        });
        
        t1.start();
        t2.start();
        
        try {
            t1.join();
            t2.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        
        System.out.println("✓ 一次性获取所有锁，避免占有等待");
    }
    
    public static void main(String[] args) {
        System.out.println("=== 死锁检测与避免 ===\n");
        
        // 演示 1：创建死锁
        System.out.println("【演示 1】经典死锁场景");
        System.out.println("两个线程，两把锁，交叉获取 → 死锁");
        System.out.println();
        
        // 取消注释以下行可以演示死锁（程序会卡住，需要手动 kill）
        // createDeadlock();
        
        // 演示 2：使用 ThreadMXBean 检测死锁
        System.out.println("【演示 2】使用 ThreadMXBean 检测死锁");
        System.out.println("代码：ManagementFactory.getThreadMXBean().findDeadlockedThreads()");
        System.out.println("命令行：jstack <pid> | grep -i deadlock");
        System.out.println();
        
        // 演示 3：避免策略
        lockOrdering();
        tryLockTimeout();
        acquireAllLocks();
        
        System.out.println("\n=== 生产环境建议 ===");
        System.out.println("1. 设计阶段：定义锁的获取顺序文档");
        System.out.println("2. 代码审查：检查多线程锁的获取顺序");
        System.out.println("3. 运行时监控：定期调用 ThreadMXBean 检测死锁");
        System.out.println("4. 超时机制：使用 tryLock 而不是 lock，设置合理超时");
        System.out.println("5. 锁粒度：尽量减小锁的范围，降低死锁概率");
    }
}
