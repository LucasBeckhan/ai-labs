import java.util.Arrays;
import java.util.List;
import java.util.function.*;

/**
 * Lambda 表达式基础
 * 
 * 核心概念：
 * 1. Lambda 是匿名函数，可以赋值给变量、作为参数传递
 * 2. 只能实现函数式接口（只有一个抽象方法的接口）
 * 3. 语法：(参数) -> { 表达式/代码块 }
 * 
 * 面试重点：
 * - Lambda 与匿名内部类的区别（编译产物、this 指向、性能）
 * - 变量捕获规则（effectively final）
 * - 方法引用的 4 种形式
 */
public class LambdaBasics {
    
    // ========== 1. Lambda 语法演进 ==========
    
    // 匿名内部类（Java 8 之前）
    interface Calculator {
        int calculate(int a, int b);
    }
    
    // ========== 2. 函数式接口 ==========
    
    @FunctionalInterface  // 编译时检查：只能有一个抽象方法
    interface MyPredicate<T> {
        boolean test(T t);
    }
    
    // ========== 3. 内置函数式接口 ==========
    // Java 8 提供 43 个内置函数式接口，常用的有：
    
    // Predicate<T>：判断型，T -> boolean
    // Function<T, R>：转换型，T -> R
    // Consumer<T>：消费型，T -> void
    // Supplier<T>：供给型，() -> T
    
    public void demonstrateThis() {
        // this 指向不同
        Runnable lambda = () -> System.out.println("Lambda this: " + this.getClass().getSimpleName());
        Runnable anonymous = new Runnable() {
            @Override
            public void run() {
                System.out.println("Anonymous this: " + this.getClass().getSimpleName());
            }
        };
        
        lambda.run();
        anonymous.run();
        System.out.println("Lambda 的 this 指向外部类，匿名类的 this 指向自身");
        System.out.println();
    }
    
    public static void main(String[] args) {
        System.out.println("=== Lambda 表达式基础 ===\n");
        
        // ========== 演示 1：Lambda 语法演进 ==========
        System.out.println("【演示 1】Lambda 语法演进");
        
        // 匿名内部类
        Calculator calc1 = new Calculator() {
            @Override
            public int calculate(int a, int b) {
                return a + b;
            }
        };
        System.out.println("匿名内部类：calc1.calculate(2, 3) = " + calc1.calculate(2, 3));
        
        // Lambda 完整写法
        Calculator calc2 = (int a, int b) -> {
            return a + b;
        };
        System.out.println("Lambda 完整写法：calc2.calculate(2, 3) = " + calc2.calculate(2, 3));
        
        // Lambda 简化写法（类型推断 + 单行省略 return）
        Calculator calc3 = (a, b) -> a + b;
        System.out.println("Lambda 简化写法：calc3.calculate(2, 3) = " + calc3.calculate(2, 3));
        System.out.println();
        
        // ========== 演示 2：自定义函数式接口 ==========
        System.out.println("【演示 2】自定义函数式接口");
        
        MyPredicate<Integer> isPositive = n -> n > 0;
        System.out.println("isPositive.test(5) = " + isPositive.test(5));
        System.out.println("isPositive.test(-3) = " + isPositive.test(-3));
        
        MyPredicate<String> isNotEmpty = s -> s != null && !s.isEmpty();
        System.out.println("isNotEmpty.test(\"hello\") = " + isNotEmpty.test("hello"));
        System.out.println("isNotEmpty.test(\"\") = " + isNotEmpty.test(""));
        System.out.println();
        
        // ========== 演示 3：内置函数式接口 ==========
        System.out.println("【演示 3】内置函数式接口");
        
        // Predicate：判断型
        Predicate<Integer> isEven = n -> n % 2 == 0;
        System.out.println("Predicate: isEven.test(4) = " + isEven.test(4));
        
        // Function：转换型
        Function<String, Integer> strLength = s -> s.length();
        System.out.println("Function: strLength.apply(\"hello\") = " + strLength.apply("hello"));
        
        // Consumer：消费型
        Consumer<String> printer = s -> System.out.println("Consumer: " + s);
        printer.accept("hello world");
        
        // Supplier：供给型
        Supplier<Double> random = () -> Math.random();
        System.out.println("Supplier: random.get() = " + random.get());
        System.out.println();
        
        // ========== 演示 4：变量捕获（effectively final）==========
        System.out.println("【演示 4】变量捕获");
        
        int factor = 10;  // effectively final（没有显式 final，但从未修改）
        
        Function<Integer, Integer> multiplier = n -> n * factor;
        System.out.println("捕获外部变量：multiplier.apply(5) = " + multiplier.apply(5));
        
        // factor = 20;  // 编译错误：Lambda 中使用的变量必须是 effectively final
        
        System.out.println("规则：Lambda 中使用的局部变量必须是 final 或 effectively final");
        System.out.println("原因：Lambda 可能在不同线程执行，避免并发修改问题");
        System.out.println();
        
        // ========== 演示 5：方法引用（4 种形式）==========
        System.out.println("【演示 5】方法引用（4 种形式）");
        
        List<String> names = Arrays.asList("alice", "bob", "charlie");
        
        // 1. 静态方法引用：ClassName::staticMethod
        Function<String, String> toUpper = String::toUpperCase;
        System.out.println("静态方法引用：String::toUpperCase");
        names.stream().map(toUpper).forEach(n -> System.out.println("  " + n));
        
        // 2. 实例方法引用（特定对象）：instance::method
        String prefix = "Hello, ";
        Function<String, String> greet = prefix::concat;
        System.out.println("\n实例方法引用：prefix::concat");
        System.out.println("  " + greet.apply("Alice"));
        
        // 3. 实例方法引用（任意对象）：ClassName::method
        Function<String, Integer> length = String::length;
        System.out.println("\n实例方法引用：String::length");
        names.stream().map(length).forEach(len -> System.out.println("  长度: " + len));
        
        // 4. 构造方法引用：ClassName::new
        Supplier<List<String>> listFactory = java.util.ArrayList::new;
        System.out.println("\n构造方法引用：ArrayList::new");
        List<String> newList = listFactory.get();
        System.out.println("  创建了新列表: " + newList.getClass().getSimpleName());
        System.out.println();
        
        // ========== 演示 6：Lambda 在集合中的应用 ==========
        System.out.println("【演示 6】Lambda 在集合中的应用");
        
        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
        
        // forEach
        System.out.print("forEach: ");
        numbers.forEach(n -> System.out.print(n + " "));
        System.out.println();
        
        // removeIf
        List<Integer> mutableNumbers = new java.util.ArrayList<>(numbers);
        mutableNumbers.removeIf(n -> n % 2 == 0);
        System.out.println("removeIf (移除偶数): " + mutableNumbers);
        
        // sort
        List<String> words = Arrays.asList("banana", "apple", "cherry");
        words.sort(String::compareToIgnoreCase);
        System.out.println("sort (忽略大小写): " + words);
        
        // replaceAll
        List<Integer> doubled = new java.util.ArrayList<>(numbers);
        doubled.replaceAll(n -> n * 2);
        System.out.println("replaceAll (翻倍): " + doubled);
        System.out.println();
        
        // ========== 演示 7：闭包与副作用 ==========
        System.out.println("【演示 7】闭包与副作用");
        
        // 错误示例：Lambda 中修改外部变量（虽然能编译，但不推荐）
        int[] counter = {0};  // 用数组绕过 effectively final 限制
        Runnable increment = () -> counter[0]++;
        
        increment.run();
        increment.run();
        increment.run();
        System.out.println("counter[0] = " + counter[0]);
        System.out.println("警告：这种方式破坏了 Lambda 的无副作用原则");
        System.out.println("推荐：使用 AtomicInteger 或避免修改外部状态");
        System.out.println();
        
        // ========== 演示 8：Lambda vs 匿名类 ==========
        System.out.println("【演示 8】Lambda vs 匿名类");
        
        // 创建实例来演示 this 指向
        LambdaBasics instance = new LambdaBasics();
        instance.demonstrateThis();
        
        System.out.println("\n=== Lambda 最佳实践 ===");
        System.out.println("1. 保持简洁：Lambda 体不超过 3 行，否则提取为方法");
        System.out.println("2. 避免副作用：不要修改外部变量");
        System.out.println("3. 使用方法引用：比 Lambda 更简洁（如 String::toUpperCase）");
        System.out.println("4. 明确类型：复杂 Lambda 加上参数类型提高可读性");
        System.out.println("5. 避免嵌套：嵌套 Lambda 难以理解，拆分为方法");
    }
}
