/**
 * CountMinSketch 频率估计
 * 用途：估计流式数据中元素的出现频率
 * 特点：高估不低估（overestimate），误差与总流量成正比
 */
public class CountMinSketchDemo {
    private int[][] table;  // d 行 w 列的计数表
    private int d;          // 深度（哈希函数个数）
    private int w;          // 宽度（每个哈希函数的范围）

    /**
     * @param d 深度（哈希函数个数，越多误差越小）
     * @param w 宽度（每个哈希函数的范围，越大碰撞越少）
     */
    public CountMinSketchDemo(int d, int w) {
        this.d = d;
        this.w = w;
        this.table = new int[d][w];
    }

    /**
     * 添加元素：d 个哈希函数各计算一个位置，对应位置 +1
     */
    public void add(String element, int count) {
        for (int i = 0; i < d; i++) {
            int hash = hash(element, i);
            int index = Math.abs(hash % w);
            table[i][index] += count;
        }
    }

    public void add(String element) {
        add(element, 1);
    }

    /**
     * 查询频率：取 d 个位置的最小值（最小化碰撞影响）
     */
    public int estimate(String element) {
        int min = Integer.MAX_VALUE;
        for (int i = 0; i < d; i++) {
            int hash = hash(element, i);
            int index = Math.abs(hash % w);
            min = Math.min(min, table[i][index]);
        }
        return min;
    }

    /**
     * 简单哈希函数（通过 seed 模拟多个哈希）
     */
    private int hash(String element, int seed) {
        int hash = 0;
        for (char c : element.toCharArray()) {
            hash = hash * 31 + c + seed * 17;
        }
        return hash;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        CountMinSketchDemo cms = new CountMinSketchDemo(5, 1000);

        System.out.println("=== CountMinSketch 频率估计 ===");
        // 模拟流式数据
        String[] stream = {"apple", "banana", "apple", "cherry", "apple", "banana", "apple"};
        for (String item : stream) {
            cms.add(item);
        }

        System.out.println("流数据: apple×4, banana×2, cherry×1");
        System.out.printf("查询 'apple' 频率 → %d（实际 4）%n", cms.estimate("apple"));
        System.out.printf("查询 'banana' 频率 → %d（实际 2）%n", cms.estimate("banana"));
        System.out.printf("查询 'cherry' 频率 → %d（实际 1）%n", cms.estimate("cherry"));
        System.out.printf("查询 'grape' 频率 → %d（实际 0，可能高估）%n", cms.estimate("grape"));

        // 大规模测试
        System.out.println("\n大规模测试：");
        CountMinSketchDemo cms2 = new CountMinSketchDemo(5, 10000);
        for (int i = 0; i < 100000; i++) {
            cms2.add("item_" + (i % 100));  // 100 个不同元素，每个约 1000 次
        }
        int estimated = cms2.estimate("item_50");
        System.out.printf("实际频率: 1000, 估计频率: %d, 误差: %d%n",
            estimated, estimated - 1000);
    }
}
