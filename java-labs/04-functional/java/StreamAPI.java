import java.util.*;
import java.util.stream.*;

/**
 * Stream API 实战演示
 * 
 * 核心概念：
 * 1. Stream 是数据通道，用于处理集合、数组等数据源
 * 2. 操作分为中间操作（返回 Stream）和终端操作（返回结果）
 * 3. 中间操作是惰性的，只有终端操作触发执行
 * 4. Stream 是一次性的，消费后不能再用
 * 
 * 面试重点：
 * - 中间操作 vs 终端操作的区别
 * - 并行流的适用场景和陷阱
 * - Collectors 的常用收集器
 */
public class StreamAPI {
    
    // 用户类（用于演示对象流）
    static class User {
        String name;
        int age;
        String city;
        
        User(String name, int age, String city) {
            this.name = name;
            this.age = age;
            this.city = city;
        }
        
        @Override
        public String toString() {
            return String.format("User(%s, %d, %s)", name, age, city);
        }
    }
    
    public static void main(String[] args) {
        System.out.println("=== Stream API 实战 ===\n");
        
        // ========== 1. Stream 创建方式 ==========
        System.out.println("【演示 1】Stream 创建方式");
        
        // 从集合创建
        List<Integer> list = Arrays.asList(1, 2, 3, 4, 5);
        Stream<Integer> stream1 = list.stream();
        System.out.println("从集合创建: list.stream()");
        
        // 从数组创建
        Integer[] array = {1, 2, 3, 4, 5};
        Stream<Integer> stream2 = Arrays.stream(array);
        System.out.println("从数组创建: Arrays.stream(array)");
        
        // 使用 Stream.of
        Stream<String> stream3 = Stream.of("a", "b", "c");
        System.out.println("使用 Stream.of: Stream.of(\"a\", \"b\", \"c\")");
        
        // 生成无限流
        Stream<Integer> stream4 = Stream.generate(() -> (int)(Math.random() * 100)).limit(5);
        System.out.println("生成无限流: Stream.generate(() -> random).limit(5)");
        
        // 迭代流
        Stream<Integer> stream5 = Stream.iterate(0, n -> n + 2).limit(5);
        System.out.println("迭代流: Stream.iterate(0, n -> n + 2).limit(5)");
        System.out.println();
        
        // ========== 2. 中间操作（Intermediate）==========
        System.out.println("【演示 2】中间操作");
        
        List<User> users = Arrays.asList(
            new User("Alice", 25, "Beijing"),
            new User("Bob", 30, "Shanghai"),
            new User("Charlie", 20, "Beijing"),
            new User("David", 35, "Guangzhou"),
            new User("Eve", 28, "Shanghai")
        );
        
        // filter：过滤
        List<User> beijingUsers = users.stream()
            .filter(u -> "Beijing".equals(u.city))
            .collect(Collectors.toList());
        System.out.println("filter (北京用户): " + beijingUsers);
        
        // map：转换
        List<String> names = users.stream()
            .map(u -> u.name)
            .collect(Collectors.toList());
        System.out.println("map (提取名字): " + names);
        
        // flatMap：展平
        List<List<Integer>> nestedList = Arrays.asList(
            Arrays.asList(1, 2),
            Arrays.asList(3, 4, 5),
            Arrays.asList(6, 7)
        );
        List<Integer> flatList = nestedList.stream()
            .flatMap(Collection::stream)
            .collect(Collectors.toList());
        System.out.println("flatMap (展平嵌套): " + flatList);
        
        // distinct：去重
        List<Integer> duplicates = Arrays.asList(1, 2, 2, 3, 3, 3);
        List<Integer> unique = duplicates.stream()
            .distinct()
            .collect(Collectors.toList());
        System.out.println("distinct (去重): " + unique);
        
        // sorted：排序
        List<Integer> unsorted = Arrays.asList(3, 1, 4, 1, 5, 9);
        List<Integer> sorted = unsorted.stream()
            .sorted()
            .collect(Collectors.toList());
        System.out.println("sorted (排序): " + sorted);
        
        // 自定义排序（按年龄降序）
        List<User> sortedByAge = users.stream()
            .sorted((u1, u2) -> u2.age - u1.age)
            .collect(Collectors.toList());
        System.out.println("sorted (按年龄降序): " + sortedByAge);
        
        // limit/skip：分页
        List<User> page2 = users.stream()
            .skip(2)
            .limit(2)
            .collect(Collectors.toList());
        System.out.println("skip(2).limit(2) (第 2 页): " + page2);
        
        // peek：调试（不改变流）
        System.out.print("peek (调试输出): ");
        users.stream()
            .filter(u -> u.age > 25)
            .peek(u -> System.out.print(u.name + " "))
            .collect(Collectors.toList());
        System.out.println();
        System.out.println();
        
        // ========== 3. 终端操作（Terminal）==========
        System.out.println("【演示 3】终端操作");
        
        // forEach：遍历
        System.out.print("forEach: ");
        users.stream().limit(3).forEach(u -> System.out.print(u.name + " "));
        System.out.println();
        
        // count：计数
        long count = users.stream().filter(u -> u.age > 25).count();
        System.out.println("count (年龄 > 25): " + count);
        
        // min/max：最值
        Optional<User> oldest = users.stream()
            .max(Comparator.comparingInt(u -> u.age));
        oldest.ifPresent(u -> System.out.println("max (最年长): " + u));
        
        // reduce：归约
        int sum = users.stream()
            .map(u -> u.age)
            .reduce(0, Integer::sum);
        System.out.println("reduce (年龄总和): " + sum);
        
        // collect：收集
        Map<String, List<User>> byCity = users.stream()
            .collect(Collectors.groupingBy(u -> u.city));
        System.out.println("collect (按城市分组): " + byCity);
        
        // match：匹配
        boolean anyOver30 = users.stream().anyMatch(u -> u.age > 30);
        boolean allOver18 = users.stream().allMatch(u -> u.age > 18);
        boolean noneOver40 = users.stream().noneMatch(u -> u.age > 40);
        System.out.println("anyMatch (>30): " + anyOver30);
        System.out.println("allMatch (>18): " + allOver18);
        System.out.println("noneMatch (>40): " + noneOver40);
        
        // findFirst/findAny：查找
        Optional<User> first = users.stream().findFirst();
        first.ifPresent(u -> System.out.println("findFirst: " + u));
        System.out.println();
        
        // ========== 4. Collectors 收集器 ==========
        System.out.println("【演示 4】Collectors 收集器");
        
        // toList/toSet/toMap
        List<String> nameList = users.stream()
            .map(u -> u.name)
            .collect(Collectors.toList());
        System.out.println("toList: " + nameList);
        
        Map<String, Integer> nameAgeMap = users.stream()
            .collect(Collectors.toMap(u -> u.name, u -> u.age));
        System.out.println("toMap: " + nameAgeMap);
        
        // groupingBy：分组
        Map<String, Long> cityCount = users.stream()
            .collect(Collectors.groupingBy(u -> u.city, Collectors.counting()));
        System.out.println("groupingBy (城市人数): " + cityCount);
        
        // partitioningBy：分区（布尔条件）
        Map<Boolean, List<User>> agePartition = users.stream()
            .collect(Collectors.partitioningBy(u -> u.age >= 25));
        System.out.println("partitioningBy (>=25): " + agePartition);
        
        // summarizingInt：统计
        IntSummaryStatistics stats = users.stream()
            .collect(Collectors.summarizingInt(u -> u.age));
        System.out.println("summarizingInt: " + stats);
        System.out.println("  count=" + stats.getCount() + 
                         ", sum=" + stats.getSum() + 
                         ", min=" + stats.getMin() + 
                         ", max=" + stats.getMax() + 
                         ", avg=" + String.format("%.2f", stats.getAverage()));
        
        // joining：字符串连接
        String joinedNames = users.stream()
            .map(u -> u.name)
            .collect(Collectors.joining(", ", "[", "]"));
        System.out.println("joining: " + joinedNames);
        System.out.println();
        
        // ========== 5. 并行流（Parallel Stream）==========
        System.out.println("【演示 5】并行流");
        
        List<Integer> numbers = IntStream.range(1, 1_000_000)
            .boxed()
            .collect(Collectors.toList());
        
        // 串行流
        long start = System.currentTimeMillis();
        long sum1 = numbers.stream()
            .filter(n -> n % 2 == 0)
            .mapToLong(n -> n * n)
            .sum();
        long time1 = System.currentTimeMillis() - start;
        System.out.println("串行流: sum=" + sum1 + ", 耗时=" + time1 + "ms");
        
        // 并行流
        start = System.currentTimeMillis();
        long sum2 = numbers.parallelStream()
            .filter(n -> n % 2 == 0)
            .mapToLong(n -> n * n)
            .sum();
        long time2 = System.currentTimeMillis() - start;
        System.out.println("并行流: sum=" + sum2 + ", 耗时=" + time2 + "ms");
        
        System.out.println("加速比: " + String.format("%.2f", (double)time1 / time2));
        System.out.println();
        
        // 并行流陷阱
        System.out.println("【并行流陷阱】");
        System.out.println("1. 线程不安全：不要在 Lambda 中修改共享变量");
        
        // 错误示例
        List<Integer> unsafeList = new ArrayList<>();
        IntStream.range(0, 1000).parallel().forEach(unsafeList::add);
        System.out.println("   预期 1000 个元素，实际: " + unsafeList.size() + "（可能丢失）");
        
        // 正确做法
        List<Integer> safeList = Collections.synchronizedList(new ArrayList<>());
        IntStream.range(0, 1000).parallel().forEach(safeList::add);
        System.out.println("   使用 synchronizedList: " + safeList.size() + "（安全）");
        
        System.out.println("2. 顺序问题：forEach 不保证顺序，用 forEachOrdered");
        System.out.print("   forEach (无序): ");
        IntStream.range(0, 10).parallel().forEach(n -> System.out.print(n + " "));
        System.out.println();
        System.out.print("   forEachOrdered (有序): ");
        IntStream.range(0, 10).parallel().forEachOrdered(n -> System.out.print(n + " "));
        System.out.println();
        System.out.println();
        
        // ========== 6. 数值流（IntStream/LongStream/DoubleStream）==========
        System.out.println("【演示 6】数值流");
        
        // IntStream
        IntStream intStream = IntStream.rangeClosed(1, 10);
        int intSum = intStream.sum();
        System.out.println("IntStream.rangeClosed(1, 10).sum() = " + intSum);
        
        // 统计信息
        IntSummaryStatistics intStats = IntStream.of(1, 2, 3, 4, 5).summaryStatistics();
        System.out.println("IntStream.summaryStatistics(): " + intStats);
        
        // 与对象流转换
        IntStream ages = users.stream().mapToInt(u -> u.age);
        System.out.println("mapToInt (提取年龄): " + ages.boxed().collect(Collectors.toList()));
        System.out.println();
        
        // ========== 7. 实战案例 ==========
        System.out.println("【演示 7】实战案例");
        
        // 案例 1：统计每个城市年龄 > 25 的用户数
        Map<String, Long> cityStats = users.stream()
            .filter(u -> u.age > 25)
            .collect(Collectors.groupingBy(u -> u.city, Collectors.counting()));
        System.out.println("案例 1 - 每个城市年龄 > 25 的用户数: " + cityStats);
        
        // 案例 2：找出年龄最大的用户
        Optional<User> oldestUser = users.stream()
            .reduce((u1, u2) -> u1.age > u2.age ? u1 : u2);
        oldestUser.ifPresent(u -> System.out.println("案例 2 - 年龄最大的用户: " + u));
        
        // 案例 3：按城市分组，每组内按年龄排序
        Map<String, List<User>> citySortedUsers = users.stream()
            .collect(Collectors.groupingBy(
                u -> u.city,
                Collectors.collectingAndThen(
                    Collectors.toList(),
                    lst -> lst.stream()
                        .sorted(Comparator.comparingInt(u -> u.age))
                        .collect(Collectors.toList())
                )
            ));
        System.out.println("案例 3 - 按城市分组并排序:");
        citySortedUsers.forEach((city, userList) -> 
            System.out.println("  " + city + ": " + userList));
        
        // 案例 4：计算平均年龄
        double avgAge = users.stream()
            .mapToInt(u -> u.age)
            .average()
            .orElse(0);
        System.out.println("案例 4 - 平均年龄: " + String.format("%.2f", avgAge));
        
        System.out.println("\n=== Stream API 最佳实践 ===");
        System.out.println("1. 优先使用 Stream 而非 for 循环（声明式更清晰）");
        System.out.println("2. 小数据量（<1000）用串行流，大数据量考虑并行流");
        System.out.println("3. 避免在 Stream 中修改外部状态（副作用）");
        System.out.println("4. 复杂逻辑拆分为多个中间操作，便于调试");
        System.out.println("5. 使用 peek 调试，但最终要移除");
    }
}
