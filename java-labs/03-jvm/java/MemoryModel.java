/**
 * JVM 内存模型演示
 * 
 * JVM 运行时数据区分为：
 * 1. 线程私有：程序计数器、虚拟机栈、本地方法栈
 * 2. 线程共享：堆、方法区
 * 
 * 面试重点：
 * - 各区域存储什么内容
 * - 哪些区域会发生 OOM
 * - 对象在内存中的布局
 */
public class MemoryModel {
    
    // ========== 1. 程序计数器（PC Register）==========
    /**
     * 作用：记录当前线程执行的字节码行号
     * 特点：
     * - 线程私有
     * - 唯一不会发生 OOM 的区域
     * - 线程切换时恢复执行位置
     */
    
    // ========== 2. 虚拟机栈（VM Stack）==========
    /**
     * 作用：描述 Java 方法执行的内存模型
     * 每个方法调用创建一个栈帧（Stack Frame），包含：
     * - 局部变量表（Local Variables Table）
     * - 操作数栈（Operand Stack）
     * - 动态链接（Dynamic Linking）
     * - 方法返回地址（Return Address）
     * 
     * 异常：StackOverflowError（栈深度超限）
     */
    
    private static int stackDepth = 0;
    
    public static void stackOverflow() {
        stackDepth++;
        stackOverflow();  // 无限递归，导致栈溢出
    }
    
    // ========== 3. 本地方法栈（Native Method Stack）==========
    /**
     * 作用：为 Native 方法服务（如 System.arraycopy）
     * 与虚拟机栈类似，也可能抛出 StackOverflowError 和 OOM
     */
    
    // ========== 4. 堆（Heap）==========
    /**
     * 作用：存放对象实例，是 GC 的主要区域
     * 
     * 分代结构（JDK 8）：
     * - 新生代（Young Generation）：1/3 堆空间
     *   - Eden：80%
     *   - Survivor0：10%
     *   - Survivor1：10%
     * - 老年代（Old Generation）：2/3 堆空间
     * 
     * 异常：OutOfMemoryError: Java heap space
     */
    
    public static void heapOOM() {
        java.util.List<byte[]> list = new java.util.ArrayList<>();
        while (true) {
            list.add(new byte[1024 * 1024]);  // 每次分配 1MB
        }
    }
    
    // ========== 5. 方法区（Method Area）==========
    /**
     * 作用：存储类信息、常量、静态变量、JIT 编译后的代码
     * 
     * JDK 7 及之前：永久代（PermGen）
     * JDK 8 及之后：元空间（Metaspace），使用本地内存
     * 
     * 异常：
     * - JDK 7: OutOfMemoryError: PermGen space
     * - JDK 8+: OutOfMemoryError: Metaspace
     */
    
    public static void metaspaceOOM() {
        // 动态生成大量类（使用 CGLIB 或 ASM）
        // 这里简化演示，实际场景：反射、动态代理、JSP 编译
        while (true) {
            // 模拟类加载（实际需要用 ClassLoader 动态生成类）
            new Object() {};  // 匿名内部类
        }
    }
    
    // ========== 对象内存布局 ==========
    /**
     * 对象在堆中的内存布局：
     * 1. 对象头（Object Header）：12-16 字节
     *    - Mark Word：8 字节（哈希码、GC 分代年龄、锁状态）
     *    - Klass Pointer：4-8 字节（指向类元数据）
     * 2. 实例数据（Instance Data）：对齐到 8 字节的倍数
     * 3. 对齐填充（Padding）：确保总大小是 8 的倍数
     */
    
    static class ObjectLayout {
        boolean flag;      // 1 字节
        int number;        // 4 字节
        long value;        // 8 字节
        Object reference;  // 4-8 字节（压缩指针）
    }
    
    // ========== 对象访问定位 ==========
    /**
     * 栈上的 reference 如何访问堆中的对象：
     * 1. 句柄访问（Handle）：reference → 句柄池 → 对象地址
     * 2. 直接指针（HotSpot）：reference → 对象地址
     *    优势：节省一次指针定位，速度更快
     */
    
    public static void main(String[] args) {
        System.out.println("=== JVM 内存模型演示 ===\n");
        
        // 1. 演示栈溢出
        System.out.println("【1. 虚拟机栈溢出】");
        try {
            stackDepth = 0;
            stackOverflow();
        } catch (StackOverflowError e) {
            System.out.println("✓ StackOverflowError 触发，递归深度: " + stackDepth);
            System.out.println("  原因：栈帧过多，超过 -Xss 限制（默认 1MB）");
            System.out.println("  解决：增加 -Xss 或优化递归（改迭代）\n");
        }
        
        // 2. 演示堆溢出（注释掉，避免程序崩溃）
        System.out.println("【2. 堆内存溢出】");
        System.out.println("  触发条件：对象过多，超过 -Xmx 限制");
        System.out.println("  解决：增加 -Xmx 或优化内存使用");
        System.out.println("  命令：java -Xms512m -Xmx1024m -XX:+HeapDumpOnOutOfMemoryError MemoryModel");
        // heapOOM();  // 取消注释可触发
        System.out.println();
        
        // 3. 演示方法区溢出（注释掉，避免程序崩溃）
        System.out.println("【3. 方法区溢出】");
        System.out.println("  JDK 7: PermGen space（-XX:MaxPermSize）");
        System.out.println("  JDK 8+: Metaspace（-XX:MaxMetaspaceSize）");
        System.out.println("  触发条件：动态生成大量类（反射、CGLIB）");
        System.out.println("  解决：增加 Metaspace 大小或减少动态类生成");
        // metaspaceOOM();  // 取消注释可触发
        System.out.println();
        
        // 4. 对象内存布局分析
        System.out.println("【4. 对象内存布局】");
        ObjectLayout obj = new ObjectLayout();
        System.out.println("  字段布局：");
        System.out.println("    - boolean flag:     1 字节");
        System.out.println("    - int number:       4 字节");
        System.out.println("    - long value:       8 字节");
        System.out.println("    - Object reference: 4-8 字节");
        System.out.println("  总大小：对象头(12-16) + 实例数据(17-21) + 对齐填充");
        System.out.println("  实际大小：约 32-40 字节（8 字节对齐）\n");
        
        // 5. 运行时数据区总结
        System.out.println("【5. 运行时数据区总结】");
        System.out.println("  ┌─────────────────────────────────────┐");
        System.out.println("  │ 线程私有                            │");
        System.out.println("  │  ├─ 程序计数器（不会 OOM）          │");
        System.out.println("  │  ├─ 虚拟机栈（StackOverflow/OOM）   │");
        System.out.println("  │  └─ 本地方法栈（StackOverflow/OOM） │");
        System.out.println("  ├─────────────────────────────────────┤");
        System.out.println("  │ 线程共享                            │");
        System.out.println("  │  ├─ 堆（OOM: Java heap space）      │");
        System.out.println("  │  └─ 方法区（OOM: Metaspace）        │");
        System.out.println("  └─────────────────────────────────────┘");
        System.out.println();
        
        // 6. 查看当前 JVM 内存配置
        System.out.println("【6. 当前 JVM 内存配置】");
        Runtime runtime = Runtime.getRuntime();
        System.out.println("  最大堆内存: " + runtime.maxMemory() / 1024 / 1024 + " MB");
        System.out.println("  初始堆内存: " + runtime.totalMemory() / 1024 / 1024 + " MB");
        System.out.println("  空闲堆内存: " + runtime.freeMemory() / 1024 / 1024 + " MB");
        System.out.println("  可用处理器: " + runtime.availableProcessors());
        
        System.out.println("\n=== 调优建议 ===");
        System.out.println("1. 生产环境：-Xms = -Xmx（避免堆震荡）");
        System.out.println("2. 新生代：老年代 = 1:2（默认 NewRatio=2）");
        System.out.println("3. Eden：Survivor = 8:1（默认 SurvivorRatio=8）");
        System.out.println("4. 大对象直接进老年代：-XX:PretenureSizeThreshold");
        System.out.println("5. 长期存活对象晋升：-XX:MaxTenuringThreshold（默认 15）");
    }
}
