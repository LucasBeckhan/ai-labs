/**
 * GC 算法演示
 * 
 * 演示 5 种垃圾收集器：
 * 1. Serial GC - 单线程，适合客户端
 * 2. Parallel GC - 多线程，吞吐量优先（JDK 8 默认）
 * 3. CMS GC - 并发标记清除，低延迟（已废弃）
 * 4. G1 GC - 分区收集，平衡延迟和吞吐量（JDK 9+ 默认）
 * 5. ZGC - 超低延迟（JDK 11+）
 * 
 * 面试重点：
 * - 各 GC 算法的适用场景
 * - GC 日志分析
 * - 调优参数选择
 */
public class GCDemo {
    
    // ========== 1. 对象分配速率测试 ==========
    public static void allocationRateTest() {
        System.out.println("【对象分配速率测试】");
        int size = 10 * 1024;  // 10KB 对象
        int count = 100_000;
        
        long start = System.currentTimeMillis();
        for (int i = 0; i < count; i++) {
            byte[] obj = new byte[size];
            // 防止被优化掉
            if (obj.hashCode() == System.currentTimeMillis()) {
                System.out.println(obj);
            }
        }
        long elapsed = System.currentTimeMillis() - start;
        
        double totalMB = (long) count * size / 1024.0 / 1024.0;
        double rate = totalMB / (elapsed / 1000.0);
        System.out.printf("  分配 %d 个对象（每个 %dKB），总 %.1f MB%n", count, size/1024, totalMB);
        System.out.printf("  耗时 %d ms，分配速率 %.1f MB/s%n", elapsed, rate);
        System.out.println("  用途：评估 GC 压力，速率越高 GC 越频繁\n");
    }
    
    // ========== 2. GC 停顿时间测试 ==========
    public static void gcPauseTest() {
        System.out.println("【GC 停顿时间测试】");
        System.out.println("  监控 GC 事件（需要开启 GC 日志）");
        System.out.println("  命令：java -Xlog:gc*:file=gc.log GCDemo");
        System.out.println();
        
        // 触发多次 GC
        for (int i = 0; i < 5; i++) {
            // 分配大量短生命周期对象
            java.util.List<byte[]> list = new java.util.ArrayList<>();
            for (int j = 0; j < 1000; j++) {
                list.add(new byte[1024]);  // 1KB
            }
            list = null;  // 让对象可回收
            System.gc();  // 建议 GC（不保证执行）
            
            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
        
        System.out.println("  ✓ 触发 5 次 GC，查看 gc.log 分析停顿时间");
        System.out.println("  关键指标：Pause Young、Pause Full、STW 时间\n");
    }
    
    // ========== 3. 分代年龄测试 ==========
    public static void tenuringTest() {
        System.out.println("【对象分代年龄测试】");
        System.out.println("  对象在 Survivor 区每熬过一次 Minor GC，年龄 +1");
        System.out.println("  默认年龄达到 15 晋升老年代（-XX:MaxTenuringThreshold=15）");
        System.out.println();
        
        // 创建长期存活的对象
        java.util.List<Object> longLived = new java.util.ArrayList<>();
        for (int i = 0; i < 10; i++) {
            longLived.add(new byte[1024 * 1024]);  // 1MB 对象
        }
        
        // 触发多次 Minor GC
        for (int i = 0; i < 20; i++) {
            byte[] temp = new byte[10 * 1024 * 1024];  // 10MB 临时对象
            temp = null;
            System.gc();
        }
        
        System.out.println("  ✓ longLived 对象经历多次 GC，年龄逐渐增加");
        System.out.println("  年龄达到阈值后晋升老年代");
        System.out.println("  查看：jstat -gcutil <pid> 观察 S0/S1/O 区域变化\n");
    }
    
    // ========== 4. 大对象直接进老年代 ==========
    public static void largeObjectTest() {
        System.out.println("【大对象直接进老年代】");
        System.out.println("  参数：-XX:PretenureSizeThreshold=1m（大于 1MB 直接进老年代）");
        System.out.println("  目的：避免在新生代复制大对象（复制成本高）");
        System.out.println();
        
        // 分配大对象
        byte[] largeObj = new byte[2 * 1024 * 1024];  // 2MB
        System.out.println("  ✓ 分配 2MB 对象");
        System.out.println("  如果设置了 PretenureSizeThreshold=1m，该对象直接进入老年代");
        System.out.println("  查看：jmap -histo <pid> | grep byte[]\n");
    }
    
    // ========== 5. GC 日志分析示例 ==========
    public static void gcLogAnalysis() {
        System.out.println("【GC 日志分析示例】");
        System.out.println();
        System.out.println("  JDK 9+ 统一日志格式（-Xlog:gc*:file=gc.log）：");
        System.out.println("  [2024-01-01T10:00:00.123+0800][info][gc] GC(0) Pause Young (Normal)");
        System.out.println("    (G1 Evacuation Pause) 256M->128M(1024M) 15.234ms");
        System.out.println();
        System.out.println("  关键字段解读：");
        System.out.println("    - Pause Young：新生代 GC（Minor GC）");
        System.out.println("    - Pause Full：全堆 GC（Major GC / Full GC）");
        System.out.println("    - 256M->128M：GC 前堆使用 → GC 后堆使用");
        System.out.println("    - (1024M)：堆总大小");
        System.out.println("    - 15.234ms：STW 停顿时间");
        System.out.println();
        System.out.println("  性能指标：");
        System.out.println("    - GC 频率：Minor GC < 1 次/秒，Full GC < 1 次/小时");
        System.out.println("    - 停顿时间：Minor GC < 50ms，Full GC < 500ms");
        System.out.println("    - 吞吐量：应用时间 / (应用时间 + GC 时间) > 99%\n");
    }
    
    // ========== 6. GC 调优参数对比 ==========
    public static void gcTuningComparison() {
        System.out.println("【GC 调优参数对比】");
        System.out.println();
        
        System.out.println("  ┌─────────────┬──────────────┬──────────────┬──────────────┐");
        System.out.println("  │ GC 类型     │ 适用场景     │ 优势         │ 劣势         │");
        System.out.println("  ├─────────────┼──────────────┼──────────────┼──────────────┤");
        System.out.println("  │ Serial      │ 单核客户端   │ 简单、无切换 │ STW 长       │");
        System.out.println("  │ Parallel    │ 后台计算     │ 吞吐量高     │ 停顿不可控   │");
        System.out.println("  │ CMS         │ Web 服务     │ 低延迟       │ 碎片、CPU 敏感│");
        System.out.println("  │ G1          │ 通用（推荐） │ 平衡延迟吞吐 │ 内存占用高   │");
        System.out.println("  │ ZGC         │ 超大堆低延迟 │ 亚毫秒停顿   │ JDK 11+      │");
        System.out.println("  └─────────────┴──────────────┴──────────────┴──────────────┘");
        System.out.println();
        
        System.out.println("  选择建议：");
        System.out.println("    - 堆 < 100MB：Serial GC");
        System.out.println("    - 堆 100MB-2GB：Parallel GC 或 G1");
        System.out.println("    - 堆 > 2GB：G1 或 ZGC");
        System.out.println("    - 延迟敏感（< 10ms）：ZGC 或 Shenandoah");
        System.out.println("    - 吞吐量优先：Parallel GC\n");
    }
    
    // ========== 7. 实时监控命令 ==========
    public static void monitoringCommands() {
        System.out.println("【GC 实时监控命令】");
        System.out.println();
        
        System.out.println("  1. jstat -gcutil <pid> 1000");
        System.out.println("     每秒打印 GC 统计：S0 S1 E O M CCS YGC YGCT FGC FGCT GCT");
        System.out.println("     - S0/S1：Survivor 区使用率");
        System.out.println("     - E：Eden 区使用率");
        System.out.println("     - O：老年代使用率");
        System.out.println("     - YGC/FGC：Young/Full GC 次数");
        System.out.println("     - YGCT/FGCT：Young/Full GC 累计耗时");
        System.out.println();
        
        System.out.println("  2. jstat -gc <pid> 1000");
        System.out.println("     详细 GC 统计（绝对值，单位 KB）");
        System.out.println();
        
        System.out.println("  3. jstat -gccause <pid> 1000");
        System.out.println("     GC 原因统计：Allocation Failure、System.gc()、Metadata GC Threshold");
        System.out.println();
        
        System.out.println("  4. jmap -heap <pid>");
        System.out.println("     查看堆配置：各区域大小、使用率、GC 算法");
        System.out.println();
        
        System.out.println("  5. jmap -histo <pid>");
        System.out.println("     查看对象直方图：按大小排序的类统计");
        System.out.println("     用途：找出占用内存最多的对象类型\n");
    }
    
    public static void main(String[] args) {
        System.out.println("=== GC 算法演示 ===\n");
        
        allocationRateTest();
        gcPauseTest();
        tenuringTest();
        largeObjectTest();
        gcLogAnalysis();
        gcTuningComparison();
        monitoringCommands();
        
        System.out.println("=== 调优实战步骤 ===");
        System.out.println("1. 监控现状：jstat -gcutil <pid> 1000");
        System.out.println("2. 分析问题：GC 频繁？停顿长？内存泄漏？");
        System.out.println("3. 选择 GC：根据堆大小和延迟要求");
        System.out.println("4. 调整参数：-Xms -Xmx -XX:+UseG1GC 等");
        System.out.println("5. 验证效果：对比调优前后的 GC 日志");
        System.out.println("6. 持续监控：生产环境定期观察\n");
        
        System.out.println("=== 常见问题排查 ===");
        System.out.println("Q1: GC 频繁但内存充足？");
        System.out.println("  → 检查新生代是否太小，对象过早晋升老年代");
        System.out.println();
        System.out.println("Q2: Full GC 频繁？");
        System.out.println("  → 检查是否有内存泄漏、大对象、Metaspace 不足");
        System.out.println();
        System.out.println("Q3: GC 停顿时间过长？");
        System.out.println("  → 切换低延迟 GC（G1/ZGC），调整目标停顿时间");
        System.out.println();
        System.out.println("Q4: 吞吐量不足？");
        System.out.println("  → 使用 Parallel GC，增加堆大小，减少 GC 频率");
    }
}
