/**
 * Lab 01 配套示例 —— 观察"JVM 在容器里如何感知内存限额"的最小程序。
 *
 * 为什么写这个程序？
 *   Java 应用迁入 K8s/容器的第一大坑就是内存：JVM 默认按"宿主机内存"来计算堆上限，
 *   在 512MB 的容器里按 16GB 宿主机算堆 → 真实分配内存超过 cgroup 限额 → 被 OOMKilled(exit 137)。
 *   本程序把关键数字打印出来，让你"亲眼看见"限额是否被感知（配合 README 的实验步骤）。
 *
 * 运行方式见同目录 Dockerfile 与 lab01 README：
 *   docker run --rm --memory=512m hello:v1     → max heap ≈ 512×75%
 *   docker run --rm --entrypoint java hello:v1 -XX:-UseContainerSupport ... → 堆按宿主机内存算（反面教材）
 */
public class Hello {

    public static void main(String[] args) throws Exception {
        // Runtime 是 JVM 运行时的管理接口，内存三兄弟：
        //   maxMemory()   = 堆上限（-Xmx 或 MaxRAMPercentage 换算后的值）
        //   totalMemory() = 当前已向 OS 申请的堆大小（会随使用逐步扩张）
        //   freeMemory()  = totalMemory 中还没被使用的部分
        Runtime rt = Runtime.getRuntime();
        long maxHeapMB = rt.maxMemory() / 1024 / 1024;

        // 关键观察点 1：max heap 是否等于 "容器限额 × MaxRAMPercentage"？
        //   是 → JVM 感知了 cgroup 限额（UseContainerSupport 生效，JDK 8u191+/10+ 默认开启）
        //   远大于容器限额 → JVM 按"宿主机内存"算了，上线必出 OOMKilled 事故
        System.out.println("[Hello] JVM max heap = " + maxHeapMB + " MB");

        // 关键观察点 2：运行用户。生产镜像禁止 root 运行（缩小被攻击后的影响面），
        // Dockerfile 里用 adduser 创建的 app 用户应出现在这里
        System.out.println("[Hello] user = " + System.getProperty("user.name"));

        // 每 5 秒打印一次当前堆使用量 —— 让 `docker logs -f` / `kubectl logs -f` 有持续输出可观察，
        // 同时保持进程存活，方便做探针、OOM 等实验
        int i = 0;
        while (true) {
            i++;
            // used = totalMemory - freeMemory：当前真正"占着"的堆空间
            System.out.println("[Hello] alive, tick=" + i
                    + ", used=" + (rt.totalMemory() - rt.freeMemory()) / 1024 / 1024 + "MB");
            Thread.sleep(5000);
        }
    }
}
