import java.util.*;

/**
 * 专题 08：图
 * 包含三道经典题的实现：BFS/DFS 遍历、拓扑排序（课程表）、岛屿数量
 */
public class Solution {

    /**
     * 题 1a：BFS 遍历（邻接表）
     * 时间 O(V+E)，空间 O(V)
     */
    public static List<Integer> bfs(Map<Integer, List<Integer>> graph, int start) {
        List<Integer> result = new ArrayList<>();
        Set<Integer> visited = new HashSet<>();
        Queue<Integer> queue = new LinkedList<>();
        
        queue.offer(start);
        visited.add(start);
        
        while (!queue.isEmpty()) {
            int node = queue.poll();
            result.add(node);
            for (int neighbor : graph.getOrDefault(node, Collections.emptyList())) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    queue.offer(neighbor);
                }
            }
        }
        return result;
    }

    /**
     * 题 1b：DFS 遍历（递归）
     * 时间 O(V+E)，空间 O(V)
     */
    public static List<Integer> dfs(Map<Integer, List<Integer>> graph, int start) {
        List<Integer> result = new ArrayList<>();
        Set<Integer> visited = new HashSet<>();
        dfsHelper(graph, start, visited, result);
        return result;
    }
    
    private static void dfsHelper(Map<Integer, List<Integer>> graph, int node, 
                                  Set<Integer> visited, List<Integer> result) {
        visited.add(node);
        result.add(node);
        for (int neighbor : graph.getOrDefault(node, Collections.emptyList())) {
            if (!visited.contains(neighbor)) {
                dfsHelper(graph, neighbor, visited, result);
            }
        }
    }

    /**
     * 题 2：课程表（拓扑排序 - Kahn 算法）
     * 时间 O(V+E)，空间 O(V+E)
     * 返回是否能完成所有课程（无环）
     */
    public static boolean canFinish(int numCourses, int[][] prerequisites) {
        // 建图 + 计算入度
        Map<Integer, List<Integer>> graph = new HashMap<>();
        int[] inDegree = new int[numCourses];
        
        for (int[] pre : prerequisites) {
            int course = pre[0];
            int prerequisite = pre[1];
            graph.computeIfAbsent(prerequisite, k -> new ArrayList<>()).add(course);
            inDegree[course]++;
        }
        
        // 入度为 0 的节点入队
        Queue<Integer> queue = new LinkedList<>();
        for (int i = 0; i < numCourses; i++) {
            if (inDegree[i] == 0) {
                queue.offer(i);
            }
        }
        
        int count = 0;
        while (!queue.isEmpty()) {
            int course = queue.poll();
            count++;
            for (int next : graph.getOrDefault(course, Collections.emptyList())) {
                inDegree[next]--;
                if (inDegree[next] == 0) {
                    queue.offer(next);
                }
            }
        }
        
        return count == numCourses;  // 全部处理完说明无环
    }

    /**
     * 题 3：岛屿数量（DFS）
     * 时间 O(m×n)，空间 O(m×n)
     */
    public static int numIslands(char[][] grid) {
        if (grid == null || grid.length == 0) return 0;
        
        int m = grid.length, n = grid[0].length;
        int count = 0;
        
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == '1') {
                    count++;
                    dfs(grid, i, j, m, n);  // 标记整个岛屿
                }
            }
        }
        return count;
    }
    
    private static void dfs(char[][] grid, int i, int j, int m, int n) {
        if (i < 0 || i >= m || j < 0 || j >= n || grid[i][j] == '0') {
            return;
        }
        grid[i][j] = '0';  // 标记为已访问
        dfs(grid, i + 1, j, m, n);  // 下
        dfs(grid, i - 1, j, m, n);  // 上
        dfs(grid, i, j + 1, m, n);  // 右
        dfs(grid, i, j - 1, m, n);  // 左
    }

    // ========== 测试 ==========
    public static void main(String[] args) {
        System.out.println("=== 题 1：图的遍历 ===");
        Map<Integer, List<Integer>> graph = new HashMap<>();
        graph.put(0, Arrays.asList(1, 2));
        graph.put(1, Arrays.asList(0, 3, 4));
        graph.put(2, Arrays.asList(0, 4));
        graph.put(3, Arrays.asList(1));
        graph.put(4, Arrays.asList(1, 2));
        
        System.out.println("BFS (从 0 开始): " + bfs(graph, 0));
        System.out.println("DFS (从 0 开始): " + dfs(graph, 0));

        System.out.println("\n=== 题 2：课程表（拓扑排序）===");
        int[][] prereq1 = {{1, 0}, {2, 0}, {3, 1}, {3, 2}};
        System.out.println("4 门课, 依赖 [[1,0],[2,0],[3,1],[3,2]] → 可完成: " + canFinish(4, prereq1));
        
        int[][] prereq2 = {{1, 0}, {0, 1}};  // 有环
        System.out.println("2 门课, 依赖 [[1,0],[0,1]] → 可完成: " + canFinish(2, prereq2));

        System.out.println("\n=== 题 3：岛屿数量 ===");
        char[][] grid1 = {
            {'1', '1', '0', '0', '0'},
            {'1', '1', '0', '0', '0'},
            {'0', '0', '1', '0', '0'},
            {'0', '0', '0', '1', '1'}
        };
        System.out.println("岛屿 1 → 数量: " + numIslands(grid1));  // 3
        
        char[][] grid2 = {
            {'1', '1', '1', '1', '0'},
            {'1', '1', '0', '1', '0'},
            {'1', '1', '0', '0', '0'},
            {'0', '0', '0', '0', '0'}
        };
        System.out.println("岛屿 2 → 数量: " + numIslands(grid2));  // 1
    }
}
