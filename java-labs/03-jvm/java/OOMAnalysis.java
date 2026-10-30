/**
 * OOM 错误分析
 * 
 * 演示 4 种常见 OOM 场景：
 * 1. Java heap space - 堆内存不足
 * 2. GC overhead limit exceeded - GC 效率过低
 * 3. Metaspace - 方法区溢出
 * 4. Direct buffer memory - 直接内存溢出
 * 
 * 面试重点：
 * - OOM 触发条件和解决思路
 * - 堆转储文件分析
 * - jmap/jstat/jstack 工具使用
 */
public class OOMAnalysis {
    
    // ========== 1. Java heap space ==========
    /**
     * 触发条件：对象占用内存超过 -Xmx 限制
     * 常见原因：
     * - 内存泄漏（集合持续增长）
     * - 大对象分配（一次性加载大文件）
     * - 堆设置过小
     * 
     * 解决思路：
     * - 增加堆内存：-Xmx4g
     * - 排查内存泄漏：jmap -histo 查看大对象
     * - 分析堆转储：MAT、JProfiler
     */
    public static void heapSpaceOOM() {
        System.out.println("【1. Java heap space】");
        System.out.println("  触发条件：对象占用内存超过 -Xmx 限制");
        System.out.println();
        System.out.println("  模拟代码：");
        System.out.println("    List<byte[]> list = new ArrayList<>();");
        System.out.println("    while (true) {");
        System.out.println("        list.add(new byte[1024 * 1024]);  // 每次 1MB");
        System.out.println("    }");
        System.out.println();
        System.out.println("  排查步骤：");
        System.out.println("    1. jmap -histo <pid> | head -20  # 查看大对象");
        System.out.println("    2. jmap -dump:format=b,file=heap.hprof <pid>");
        System.out.println("    3. 用 MAT 分析 heap.hprof，找出 GC Roots");
        System.out.println();
        System.out.println("  解决方案：");
        System.out.println("    - 增加堆：-Xms4g -Xmx4g");
        System.out.println("    - 修复泄漏：检查集合、缓存、监听器");
        System.out.println("    - 优化算法：减少临时对象、复用对象\n");
    }
    
    // ========== 2. GC overhead limit exceeded ==========
    /**
     * 触发条件：98% 以上时间用于 GC，且回收内存 < 2%
     * 常见原因：
     * - 内存泄漏导致 GC 频繁但效果差
     * - 堆太小，对象太多
     * 
     * 解决思路：
     * - 增加堆内存
     * - 排查内存泄漏
     * - 禁用该检查：-XX:-UseGCOverheadLimit（不推荐）
     */
    public static void gcOverheadOOM() {
        System.out.println("【2. GC overhead limit exceeded】");
        System.out.println("  触发条件：98% 以上时间用于 GC，且回收内存 < 2%");
        System.out.println();
        System.out.println("  典型场景：");
        System.out.println("    - 堆很小（如 -Xmx10m），但对象很多");
        System.out.println("    - GC 频繁触发但回收不了多少内存");
        System.out.println("    - 应用几乎停滞，CPU 全在 GC");
        System.out.println();
        System.out.println("  排查步骤：");
        System.out.println("    1. jstat -gcutil <pid> 1000");
        System.out.println("       观察 FGC（Full GC 次数）和 FGCT（Full GC 耗时）");
        System.out.println("       如果 FGC 频繁且 FGCT 占比 > 90%，说明 GC 效率低");
        System.out.println("    2. jmap -histo <pid>");
        System.out.println("       查看哪些对象占用最多内存");
        System.out.println();
        System.out.println("  解决方案：");
        System.out.println("    - 增加堆：-Xmx4g");
        System.out.println("    - 排查泄漏：通常是内存泄漏导致");
        System.out.println("    - 禁用检查：-XX:-UseGCOverheadLimit（治标不治本）\n");
    }
    
    // ========== 3. Metaspace ==========
    /**
     * 触发条件：类元数据超过 -XX:MaxMetaspaceSize
     * 常见原因：
     * - 动态生成大量类（CGLIB、ASM、反射代理）
     * - 加载过多第三方库
     * - 热部署导致类未卸载
     * 
     * 解决思路：
     * - 增加 Metaspace：-XX:MaxMetaspaceSize=512m
     * - 减少动态类生成
     * - 启用类卸载：-XX:+CMSClassUnloadingEnabled
     */
    public static void metaspaceOOM() {
        System.out.println("【3. Metaspace（JDK 8+）】");
        System.out.println("  触发条件：类元数据超过 -XX:MaxMetaspaceSize");
        System.out.println();
        System.out.println("  典型场景：");
        System.out.println("    - Spring 大量使用 CGLIB 生成代理类");
        System.out.println("    - MyBatis 动态生成 Mapper 代理");
        System.out.println("    - Groovy/Scala 动态编译");
        System.out.println("    - Tomcat 热部署 JSP");
        System.out.println();
        System.out.println("  模拟代码（使用 CGLIB）：");
        System.out.println("    Enhancer enhancer = new Enhancer();");
        System.out.println("    enhancer.setSuperclass(OOMAnalysis.class);");
        System.out.println("    enhancer.setUseCache(false);  // 不复用，每次生成新类");
        System.out.println("    while (true) {");
        System.out.println("        enhancer.create();");
        System.out.println("    }");
        System.out.println();
        System.out.println("  排查步骤：");
        System.out.println("    1. jstat -gcutil <pid> 1000");
        System.out.println("       观察 M（Metaspace 使用率）是否接近 100%");
        System.out.println("    2. jcmd <pid> VM.classloader_stats");
        System.out.println("       查看类加载器统计");
        System.out.println("    3. jcmd <pid> VM.class_hierarchy");
        System.out.println("       查看类继承关系");
        System.out.println();
        System.out.println("  解决方案：");
        System.out.println("    - 增加 Metaspace：-XX:MaxMetaspaceSize=512m");
        System.out.println("    - 启用类卸载：-XX:+ClassUnloadingWithConcurrentMark");
        System.out.println("    - 减少动态类：使用缓存、避免重复生成\n");
    }
    
    // ========== 4. Direct buffer memory ==========
    /**
     * 触发条件：直接内存超过 -XX:MaxDirectMemorySize
     * 常见原因：
     * - NIO 使用 DirectByteBuffer
     * - Netty 默认使用直接内存
     * - 内存泄漏（DirectByteBuffer 未释放）
     * 
     * 解决思路：
     * - 增加直接内存：-XX:MaxDirectMemorySize=1g
     * - 及时释放：buffer.cleaner().clean()
     * - 使用堆内存：ByteBuffer.allocate()
     */
    public static void directBufferOOM() {
        System.out.println("【4. Direct buffer memory】");
        System.out.println("  触发条件：直接内存超过 -XX:MaxDirectMemorySize");
        System.out.println();
        System.out.println("  典型场景：");
        System.out.println("    - NIO 使用 DirectByteBuffer（零拷贝）");
        System.out.println("    - Netty 默认使用直接内存（高性能）");
        System.out.println("    - 内存泄漏：DirectByteBuffer 依赖 GC 回收");
        System.out.println();
        System.out.println("  模拟代码：");
        System.out.println("    List<ByteBuffer> list = new ArrayList<>();");
        System.out.println("    while (true) {");
        System.out.println("        list.add(ByteBuffer.allocateDirect(1024 * 1024));  // 1MB");
        System.out.println("    }");
        System.out.println();
        System.out.println("  排查步骤：");
        System.out.println("    1. jmap -histo <pid> | grep DirectByteBuffer");
        System.out.println("       查看 DirectByteBuffer 对象数量和大小");
        System.out.println("    2. jcmd <pid> VM.native_memory summary");
        System.out.println("       查看本地内存使用（需要 -XX:NativeMemoryTracking=summary）");
        System.out.println();
        System.out.println("  解决方案：");
        System.out.println("    - 增加直接内存：-XX:MaxDirectMemorySize=1g");
        System.out.println("    - 手动释放：((DirectBuffer) buffer).cleaner().clean()");
        System.out.println("    - 使用堆内存：ByteBuffer.allocate()（性能略低）");
        System.out.println("    - Netty 配置：-Dio.netty.maxDirectMemory=0（使用 JVM 限制）\n");
    }
    
    // ========== 5. 堆转储分析 ==========
    public static void heapDumpAnalysis() {
        System.out.println("【5. 堆转储分析工具】");
        System.out.println();
        
        System.out.println("  生成堆转储：");
        System.out.println("    1. OOM 时自动生成：");
        System.out.println("       -XX:+HeapDumpOnOutOfMemoryError");
        System.out.println("       -XX:HeapDumpPath=/path/to/dump.hprof");
        System.out.println();
        System.out.println("    2. 手动生成：");
        System.out.println("       jmap -dump:format=b,file=heap.hprof <pid>");
        System.out.println();
        
        System.out.println("  分析工具：");
        System.out.println("    1. Eclipse MAT（Memory Analyzer Tool）");
        System.out.println("       - 免费，功能强大");
        System.out.println("       - 自动检测内存泄漏");
        System.out.println("       - 支持 Dominator Tree、Histogram、Leak Suspects");
        System.out.println();
        System.out.println("    2. JProfiler");
        System.out.println("       - 商业软件，界面友好");
        System.out.println("       - 实时监控 + 离线分析");
        System.out.println();
        System.out.println("    3. VisualVM");
        System.out.println("       - JDK 自带，轻量级");
        System.out.println("       - 基础分析功能");
        System.out.println();
        
        System.out.println("  MAT 分析步骤：");
        System.out.println("    1. 打开 heap.hprof");
        System.out.println("    2. 查看 Leak Suspects Report（自动检测泄漏）");
        System.out.println("    3. 查看 Histogram（按类统计对象数量和大小）");
        System.out.println("    4. 查看 Dominator Tree（按对象大小排序）");
        System.out.println("    5. 右键大对象 → Path to GC Roots（找出谁持有引用）\n");
    }
    
    // ========== 6. OOM 排查流程 ==========
    public static void oomTroubleshooting() {
        System.out.println("【6. OOM 排查标准流程】");
        System.out.println();
        
        System.out.println("  步骤 1：确认 OOM 类型");
        System.out.println("    查看日志：java.lang.OutOfMemoryError: <type>");
        System.out.println("    - Java heap space → 堆内存不足");
        System.out.println("    - GC overhead limit exceeded → GC 效率低");
        System.out.println("    - Metaspace → 类加载过多");
        System.out.println("    - Direct buffer memory → 直接内存不足");
        System.out.println("    - unable to create new native thread → 线程数超限");
        System.out.println();
        
        System.out.println("  步骤 2：收集现场信息");
        System.out.println("    - 堆转储：jmap -dump:format=b,file=heap.hprof <pid>");
        System.out.println("    - 线程栈：jstack <pid> > thread.txt");
        System.out.println("    - GC 日志：-Xlog:gc*:file=gc.log");
        System.out.println("    - JVM 参数：jinfo -flags <pid>");
        System.out.println();
        
        System.out.println("  步骤 3：分析堆转储");
        System.out.println("    - 用 MAT 打开 heap.hprof");
        System.out.println("    - 查看 Leak Suspects（自动检测泄漏）");
        System.out.println("    - 查看 Histogram（找出大对象）");
        System.out.println("    - 查看 Dominator Tree（按大小排序）");
        System.out.println();
        
        System.out.println("  步骤 4：定位根因");
        System.out.println("    - 右键大对象 → Path to GC Roots");
        System.out.println("    - 找出谁持有引用（集合、缓存、监听器）");
        System.out.println("    - 检查代码逻辑（是否正确释放、是否有泄漏）");
        System.out.println();
        
        System.out.println("  步骤 5：验证修复");
        System.out.println("    - 修复代码后重新运行");
        System.out.println("    - 监控内存使用（jstat、VisualVM）");
        System.out.println("    - 压力测试验证不再 OOM\n");
    }
    
    // ========== 7. 常见 OOM 场景总结 ==========
    public static void commonScenarios() {
        System.out.println("【7. 常见 OOM 场景总结】");
        System.out.println();
        
        System.out.println("  ┌─────────────────────┬──────────────────────┬──────────────────────┐");
        System.out.println("  │ OOM 类型            │ 常见原因             │ 解决方案             │");
        System.out.println("  ├─────────────────────┼──────────────────────┼──────────────────────┤");
        System.out.println("  │ Java heap space     │ 内存泄漏、大对象     │ 增加堆、修复泄漏     │");
        System.out.println("  │ GC overhead         │ 堆太小、GC 频繁      │ 增加堆、优化对象分配 │");
        System.out.println("  │ Metaspace           │ 动态类过多           │ 增加 Metaspace       │");
        System.out.println("  │ Direct buffer       │ NIO 使用不当         │ 增加直接内存、及时释放│");
        System.out.println("  │ Native thread       │ 线程数超限           │ 增加线程数、用线程池 │");
        System.out.println("  └─────────────────────┴──────────────────────┴──────────────────────┘");
        System.out.println();
        
        System.out.println("  预防措施：");
        System.out.println("    1. 压力测试：上线前模拟真实负载");
        System.out.println("    2. 内存监控：Prometheus + Grafana 监控堆使用率");
        System.out.println("    3. 告警设置：堆使用率 > 80% 时告警");
        System.out.println("    4. 定期分析：每周查看 GC 日志，发现趋势");
        System.out.println("    5. 代码审查：检查集合、缓存、监听器是否及时清理\n");
    }
    
    public static void main(String[] args) {
        System.out.println("=== OOM 错误分析 ===\n");
        
        heapSpaceOOM();
        gcOverheadOOM();
        metaspaceOOM();
        directBufferOOM();
        heapDumpAnalysis();
        oomTroubleshooting();
        commonScenarios();
        
        System.out.println("=== 实战建议 ===");
        System.out.println("1. 生产环境必须配置：");
        System.out.println("   -XX:+HeapDumpOnOutOfMemoryError");
        System.out.println("   -XX:HeapDumpPath=/path/to/dump.hprof");
        System.out.println();
        System.out.println("2. 启动时记录 GC 日志：");
        System.out.println("   -Xlog:gc*:file=gc.log:time,uptime,level,tags");
        System.out.println();
        System.out.println("3. 定期监控：");
        System.out.println("   jstat -gcutil <pid> 1000 > gc_stats.log");
        System.out.println();
        System.out.println("4. OOM 发生后：");
        System.out.println("   - 保留 heap.hprof 和 gc.log");
        System.out.println("   - 用 MAT 分析，找出大对象");
        System.out.println("   - 修复代码，验证不再 OOM");
    }
}
