import java.util.HashSet;
import java.util.Set;

public class HyperLogLogDemo {
    private int[] registers;
    private int m;  // 寄存器数量 = 2^p
    private int p;  // 精度参数

    public HyperLogLogDemo(int p) {
        this.p = p;
        this.m = 1 << p;
        this.registers = new int[m];
    }

    private int hash(String element) {
        // 改进的哈希函数（更好的分布）
        int hash = 0x811c9dc5;  // FNV offset basis
        for (char c : element.toCharArray()) {
            hash ^= c;
            hash *= 0x01000193;  // FNV prime
        }
        return hash;
    }

    public void add(String element) {
        int hash = hash(element);
        int index = hash >>> (32 - p);  // 取高 p 位作为索引
        int remaining = hash & ((1 << (32 - p)) - 1);  // 剩余位
        
        // 计算 remaining 中从高位开始第一个 1 出现的位置（1-based）
        int leadingZeros = 1;
        if (remaining == 0) {
            leadingZeros = 32 - p + 1;  // 全是 0，位置在最后
        } else {
            // 找到第一个 1 的位置
            int mask = 1 << (31 - p);
            while ((remaining & mask) == 0) {
                leadingZeros++;
                mask >>>= 1;
                if (mask == 0) break;
            }
        }
        
        registers[index] = Math.max(registers[index], leadingZeros);
    }

    public long estimate() {
        // 调和平均数
        double sum = 0;
        int zeros = 0;
        for (int val : registers) {
            sum += 1.0 / (1L << val);  // 2^(-val)
            if (val == 0) zeros++;
        }
        
        double alpha = getAlpha(m);
        double estimate = alpha * m * m / sum;

        // 小范围修正（Linear Counting）
        if (estimate <= 2.5 * m && zeros > 0) {
            estimate = m * Math.log((double) m / zeros);
        }
        return (long) estimate;
    }

    private double getAlpha(int m) {
        switch (m) {
            case 16: return 0.673;
            case 32: return 0.697;
            case 64: return 0.709;
            default: return 0.7213 / (1 + 1.079 / m);
        }
    }

    public static void main(String[] args) {
        HyperLogLogDemo hll = new HyperLogLogDemo(10);  // 1024 个寄存器
        Set<String> actual = new HashSet<>();

        System.out.println("=== HyperLogLog 基数估计 ===");
        for (int i = 0; i < 100000; i++) {
            String element = "user_" + i;
            hll.add(element);
            actual.add(element);
        }

        long estimated = hll.estimate();
        int actualSize = actual.size();
        double error = Math.abs(estimated - actualSize) * 100.0 / actualSize;

        System.out.println("实际基数: " + actualSize);
        System.out.println("估计基数: " + estimated);
        System.out.printf("误差: %.2f%%\n", error);
    }
}
