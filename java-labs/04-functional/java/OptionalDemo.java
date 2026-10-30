import java.util.*;

/**
 * Optional 最佳实践演示
 * 
 * 核心概念：
 * 1. Optional 是一个容器，可能包含非 null 值，也可能为空
 * 2. 目的是替代 null 检查，避免 NullPointerException
 * 3. 强制调用者显式处理"值不存在"的情况
 * 
 * 面试重点：
 * - Optional 的正确用法 vs 反模式
 * - orElse vs orElseGet 的区别
 * - map/flatMap 的链式调用
 * - 什么时候该用 Optional，什么时候不该用
 */
public class OptionalDemo {
    
    // 用户类（可能为 null 的场景）
    static class User {
        String name;
        Address address;
        
        User(String name, Address address) {
            this.name = name;
            this.address = address;
        }
    }
    
    static class Address {
        String city;
        
        Address(String city) {
            this.city = city;
        }
    }
    
    // ========== 1. Optional 创建方式 ==========
    
    public static void createOptional() {
        System.out.println("【演示 1】Optional 创建方式");
        
        // of：值不能为 null
        Optional<String> opt1 = Optional.of("hello");
        System.out.println("Optional.of(\"hello\"): " + opt1);
        
        // ofNullable：值可以为 null
        Optional<String> opt2 = Optional.ofNullable(null);
        System.out.println("Optional.ofNullable(null): " + opt2);
        
        // empty：创建空 Optional
        Optional<String> opt3 = Optional.empty();
        System.out.println("Optional.empty(): " + opt3);
        System.out.println();
    }
    
    // ========== 2. 获取值的方式 ==========
    
    public static void getValue() {
        System.out.println("【演示 2】获取值的方式");
        
        Optional<String> present = Optional.of("hello");
        Optional<String> empty = Optional.empty();
        
        // get()：有值返回值，无值抛异常（慎用）
        System.out.println("present.get(): " + present.get());
        // empty.get();  // 抛出 NoSuchElementException
        
        // orElse(default)：无值返回默认值
        System.out.println("empty.orElse(\"default\"): " + empty.orElse("default"));
        
        // orElseGet(Supplier)：无值调用 Supplier 生成默认值
        System.out.println("empty.orElseGet(() -> \"generated\"): " + 
                         empty.orElseGet(() -> "generated"));
        
        // orElseThrow()：无值抛异常（Java 10+，Java 8 需要 Supplier）
        try {
            empty.orElseThrow(() -> new NoSuchElementException("No value present"));
        } catch (NoSuchElementException e) {
            System.out.println("empty.orElseThrow() 抛出异常: " + e.getClass().getSimpleName());
        }
        
        // orElseThrow(Supplier)：无值抛自定义异常
        try {
            empty.orElseThrow(() -> new RuntimeException("值不存在"));
        } catch (RuntimeException e) {
            System.out.println("empty.orElseThrow(...) 抛出异常: " + e.getMessage());
        }
        System.out.println();
    }
    
    // ========== 3. 判断是否存在 ==========
    
    public static void checkPresence() {
        System.out.println("【演示 3】判断是否存在");
        
        Optional<String> present = Optional.of("hello");
        Optional<String> empty = Optional.empty();
        
        // isPresent()：判断是否有值
        System.out.println("present.isPresent(): " + present.isPresent());
        System.out.println("empty.isPresent(): " + empty.isPresent());
        
        // isEmpty()：判断是否为空（Java 11+，Java 8 使用 !isPresent()）
        System.out.println("empty.isEmpty(): " + !empty.isPresent());
        
        // ifPresent(Consumer)：有值时执行操作
        present.ifPresent(s -> System.out.println("ifPresent: " + s));
        
        // ifPresentOrElse(Consumer, Runnable)：有值执行 A，无值执行 B（Java 9+）
        // Java 8 兼容写法：
        if (empty.isPresent()) {
            System.out.println("有值: " + empty.get());
        } else {
            System.out.println("无值，执行默认操作");
        }
        System.out.println();
    }
    
    // ========== 4. 链式操作（map/flatMap/filter）==========
    
    public static void chainOperations() {
        System.out.println("【演示 4】链式操作");
        
        // map：转换值（如果存在）
        Optional<String> name = Optional.of("alice");
        Optional<String> upperName = name.map(String::toUpperCase);
        System.out.println("map (转大写): " + upperName.orElse("N/A"));
        
        // flatMap：转换值（返回值也是 Optional，避免嵌套）
        Optional<User> user = Optional.of(new User("Bob", new Address("Beijing")));
        Optional<String> city = user.flatMap(u -> Optional.ofNullable(u.address))
                                     .map(a -> a.city);
        System.out.println("flatMap (提取城市): " + city.orElse("N/A"));
        
        // filter：过滤（不满足条件返回 empty）
        Optional<Integer> age = Optional.of(25);
        Optional<Integer> adult = age.filter(a -> a >= 18);
        System.out.println("filter (>=18): " + adult.orElse(-1));
        
        Optional<Integer> child = age.filter(a -> a < 18);
        System.out.println("filter (<18): " + child.orElse(-1));
        System.out.println();
    }
    
    // ========== 5. 实战场景：替代 null 检查 ==========
    
    public static void realWorldExample() {
        System.out.println("【演示 5】实战场景：替代多层 null 检查");
        
        User user = new User("Alice", new Address("Shanghai"));
        
        // 传统方式（丑陋且易出错）
        String city1 = "Unknown";
        if (user != null && user.address != null && user.address.city != null) {
            city1 = user.address.city;
        }
        System.out.println("传统方式: " + city1);
        
        // Optional 方式（优雅且安全）
        String city2 = Optional.ofNullable(user)
            .map(u -> u.address)
            .map(a -> a.city)
            .orElse("Unknown");
        System.out.println("Optional 方式: " + city2);
        
        // 测试 null 场景
        User userWithoutAddress = new User("Bob", null);
        String city3 = Optional.ofNullable(userWithoutAddress)
            .map(u -> u.address)
            .map(a -> a.city)
            .orElse("Unknown");
        System.out.println("user.address = null 时: " + city3);
        System.out.println();
    }
    
    // ========== 6. 反模式（避免的用法）==========
    
    public static void antiPatterns() {
        System.out.println("【演示 6】反模式（避免的用法）");
        
        Optional<String> opt = Optional.of("hello");
        
        // 反模式 1：isPresent + get（和 null 检查没区别）
        System.out.println("❌ 反模式 1: isPresent + get");
        String value1;
        if (opt.isPresent()) {
            value1 = opt.get();
        } else {
            value1 = "default";
        }
        System.out.println("   应该用: opt.orElse(\"default\")");
        
        // 反模式 2：作为字段类型（Optional 不可序列化）
        System.out.println("❌ 反模式 2: 作为类字段");
        System.out.println("   class User { Optional<String> name; }");
        System.out.println("   问题：Optional 不可序列化，增加内存开销");
        System.out.println("   应该用: String name（允许为 null）");
        
        // 反模式 3：作为方法参数
        System.out.println("❌ 反模式 3: 作为方法参数");
        System.out.println("   void process(Optional<String> opt)");
        System.out.println("   问题：调用方被迫包装 Optional，增加复杂度");
        System.out.println("   应该用: 方法重载（process() 和 process(String)）");
        
        // 反模式 4：在集合中存储 Optional
        System.out.println("❌ 反模式 4: 集合中存储 Optional");
        System.out.println("   List<Optional<String>> list");
        System.out.println("   问题：调用方需要双重检查（集合元素 + Optional）");
        System.out.println("   应该用: List<String> + filter 过滤 null");
        System.out.println();
    }
    
    // ========== 7. Optional 与 Stream 配合 ==========
    
    public static void optionalWithStream() {
        System.out.println("【演示 7】Optional 与 Stream 配合");
        
        List<Optional<String>> list = Arrays.asList(
            Optional.of("a"),
            Optional.empty(),
            Optional.of("b"),
            Optional.empty(),
            Optional.of("c")
        );
        
        // 过滤空值并提取值
        List<String> nonEmpty = list.stream()
            .filter(Optional::isPresent)
            .map(Optional::get)
            .collect(java.util.stream.Collectors.toList());
        System.out.println("过滤空值: " + nonEmpty);
        
        // Java 9+ 使用 flatMap 更简洁（Java 8 兼容写法）
        List<String> nonEmpty2 = list.stream()
            .flatMap(opt -> opt.map(java.util.stream.Stream::of).orElse(java.util.stream.Stream.empty()))
            .collect(java.util.stream.Collectors.toList());
        System.out.println("flatMap 方式: " + nonEmpty2);
        System.out.println();
    }
    
    // ========== 8. Optional 性能对比 ==========
    
    public static void performanceComparison() {
        System.out.println("【演示 8】性能对比：Optional vs null 检查");
        
        String value = "hello";
        int iterations = 10_000_000;
        
        // 传统 null 检查
        long start = System.nanoTime();
        for (int i = 0; i < iterations; i++) {
            String result = (value != null) ? value.toUpperCase() : "DEFAULT";
        }
        long time1 = System.nanoTime() - start;
        
        // Optional 方式
        start = System.nanoTime();
        for (int i = 0; i < iterations; i++) {
            String result = Optional.ofNullable(value)
                .map(String::toUpperCase)
                .orElse("DEFAULT");
        }
        long time2 = System.nanoTime() - start;
        
        System.out.println("传统 null 检查: " + time1 / 1_000_000 + " ms");
        System.out.println("Optional 方式: " + time2 / 1_000_000 + " ms");
        System.out.println("性能差异: Optional 慢约 " + (time2 / time1) + " 倍");
        System.out.println("结论：Optional 有性能开销，但对业务代码影响可忽略");
        System.out.println("      优先保证代码可读性和安全性");
        System.out.println();
    }
    
    public static void main(String[] args) {
        System.out.println("=== Optional 最佳实践 ===\n");
        
        createOptional();
        getValue();
        checkPresence();
        chainOperations();
        realWorldExample();
        antiPatterns();
        optionalWithStream();
        performanceComparison();
        
        System.out.println("=== Optional 使用指南 ===");
        System.out.println("✅ 应该使用：");
        System.out.println("   - 方法返回值（可能为 null）");
        System.out.println("   - 链式调用（map/flatMap/filter）");
        System.out.println("   - 明确表达「值可能不存在」的语义");
        System.out.println();
        System.out.println("❌ 不应该使用：");
        System.out.println("   - 类字段（不可序列化）");
        System.out.println("   - 方法参数（增加调用方复杂度）");
        System.out.println("   - 集合元素（双重检查）");
        System.out.println("   - isPresent + get（和 null 检查没区别）");
        System.out.println();
        System.out.println("💡 最佳实践：");
        System.out.println("   - 返回值用 Optional，字段用原始类型");
        System.out.println("   - 用 orElse/orElseGet 替代 isPresent + get");
        System.out.println("   - 用 map/flatMap 替代嵌套 if");
        System.out.println("   - 性能敏感场景（循环内）避免使用 Optional");
    }
}
