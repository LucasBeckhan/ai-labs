import java.util.BitSet;

/**
 * 布隆过滤器（Bloom Filter）
 * 用途：快速判断元素"可能存在"或"一定不存在"
 * 特点：假阳性（说存在可能不存在），无假阴性（说不存在一定不存在）
 */
public class BloomFilterDemo {
    private BitSet bitSet;
    private int size;          // bit 数组大小
    private int hashCount;     // 哈希函数个数

    /**
     * @param size      bit 数组大小（越大误判率越低，内存越大）
     * @param hashCount 哈希函数个数（最优值 = (size/n) * ln2）
     */
    public BloomFilterDemo(int size, int hashCount) {
        this.size = size;
        this.hashCount = hashCount;
        this.bitSet = new BitSet(size);
    }

    /**
     * 插入元素：用 hashCount 个哈希函数计算位置，全部置 1
     */
    public void add(String element) {
        for (int i = 0; i < hashCount; i++) {
            int hash = hash(element, i);
            bitSet.set(Math.abs(hash % size));
        }
    }

    /**
     * 查询元素：检查 hashCount 个位置是否全为 1
     * @return true = 可能存在，false = 一定不存在
     */
    public boolean mightContain(String element) {
        for (int i = 0; i < hashCount; i++) {
            int hash = hash(element, i);
            if (!bitSet.get(Math.abs(hash % size))) {
                return false;  // 有一个位置是 0，一定不存在
            }
        }
        return true;  // 所有位置都是 1，可能存在（有误判）
    }

    /**
     * 简单哈希函数（生产用 MurmurHash 等）
     * 通过 seed 参数模拟多个哈希函数
     */
    private int hash(String element, int seed) {
        int hash = 0;
        for (char c : element.toCharArray()) {
            hash = hash * 31 + c + seed;
        }
        return hash;
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        // 10 万元素，1% 误判率 → 约需 960 KB（约 100 万 bit），7 个哈希函数
        BloomFilterDemo filter = new BloomFilterDemo(1_000_000, 7);

        System.out.println("=== 布隆过滤器演示 ===");
        filter.add("apple");
        filter.add("banana");
        filter.add("cherry");

        System.out.println("查询 'apple' → " + filter.mightContain("apple"));       // true
        System.out.println("查询 'banana' → " + filter.mightContain("banana"));     // true
        System.out.println("查询 'orange' → " + filter.mightContain("orange"));     // false（一定不存在）
        System.out.println("查询 'grape' → " + filter.mightContain("grape"));       // false 或 true（可能误判）

        // 批量测试误判率
        int testCount = 10000;
        int falsePositives = 0;
        for (int i = 0; i < testCount; i++) {
            String test = "test_" + i;
            if (filter.mightContain(test)) {
                falsePositives++;
            }
        }
        System.out.printf("%n误判率测试：查询 %d 个未插入的元素，误判 %d 个（%.2f%%）%n",
            testCount, falsePositives, falsePositives * 100.0 / testCount);
    }
}
