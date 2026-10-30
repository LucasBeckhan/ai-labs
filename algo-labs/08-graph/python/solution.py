"""
专题 08：图
包含三道经典题的实现：BFS/DFS 遍历、拓扑排序（课程表）、岛屿数量
"""
from collections import deque, defaultdict


def bfs(graph: dict[int, list[int]], start: int) -> list[int]:
    """
    题 1a：BFS 遍历（邻接表）
    时间 O(V+E)，空间 O(V)
    """
    result = []
    visited = set([start])
    queue = deque([start])
    
    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return result


def dfs(graph: dict[int, list[int]], start: int) -> list[int]:
    """
    题 1b：DFS 遍历（递归）
    时间 O(V+E)，空间 O(V)
    """
    result = []
    visited = set()
    
    def dfs_helper(node):
        visited.add(node)
        result.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs_helper(neighbor)
    
    dfs_helper(start)
    return result


def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    """
    题 2：课程表（拓扑排序 - Kahn 算法）
    时间 O(V+E)，空间 O(V+E)
    返回是否能完成所有课程（无环）
    """
    # 建图 + 计算入度
    graph = defaultdict(list)
    in_degree = [0] * num_courses
    
    for course, prerequisite in prerequisites:
        graph[prerequisite].append(course)
        in_degree[course] += 1
    
    # 入度为 0 的节点入队
    queue = deque([i for i in range(num_courses) if in_degree[i] == 0])
    
    count = 0
    while queue:
        course = queue.popleft()
        count += 1
        for next_course in graph[course]:
            in_degree[next_course] -= 1
            if in_degree[next_course] == 0:
                queue.append(next_course)
    
    return count == num_courses  # 全部处理完说明无环


def num_islands(grid: list[list[str]]) -> int:
    """
    题 3：岛屿数量（DFS）
    时间 O(m×n)，空间 O(m×n)
    """
    if not grid:
        return 0
    
    m, n = len(grid), len(grid[0])
    count = 0
    
    def dfs(i, j):
        if i < 0 or i >= m or j < 0 or j >= n or grid[i][j] == '0':
            return
        grid[i][j] = '0'  # 标记为已访问
        dfs(i + 1, j)  # 下
        dfs(i - 1, j)  # 上
        dfs(i, j + 1)  # 右
        dfs(i, j - 1)  # 左
    
    for i in range(m):
        for j in range(n):
            if grid[i][j] == '1':
                count += 1
                dfs(i, j)  # 标记整个岛屿
    
    return count


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 题 1：图的遍历 ===")
    graph = {
        0: [1, 2],
        1: [0, 3, 4],
        2: [0, 4],
        3: [1],
        4: [1, 2]
    }
    print(f"BFS (从 0 开始): {bfs(graph, 0)}")
    print(f"DFS (从 0 开始): {dfs(graph, 0)}")

    print("\n=== 题 2：课程表（拓扑排序）===")
    prereq1 = [[1, 0], [2, 0], [3, 1], [3, 2]]
    print(f"4 门课, 依赖 {prereq1} → 可完成: {can_finish(4, prereq1)}")
    
    prereq2 = [[1, 0], [0, 1]]  # 有环
    print(f"2 门课, 依赖 {prereq2} → 可完成: {can_finish(2, prereq2)}")

    print("\n=== 题 3：岛屿数量 ===")
    grid1 = [
        ['1', '1', '0', '0', '0'],
        ['1', '1', '0', '0', '0'],
        ['0', '0', '1', '0', '0'],
        ['0', '0', '0', '1', '1']
    ]
    print(f"岛屿 1 → 数量: {num_islands(grid1)}")  # 3
    
    grid2 = [
        ['1', '1', '1', '1', '0'],
        ['1', '1', '0', '1', '0'],
        ['1', '1', '0', '0', '0'],
        ['0', '0', '0', '0', '0']
    ]
    print(f"岛屿 2 → 数量: {num_islands(grid2)}")  # 1
