# 专题 07：二分查找

> 核心思想：在有序区间上每次排除一半，把 O(n) 降到 O(log n)。关键是维护"不变量"。

## 适用场景

- 有序数组的查找（精确匹配或边界）
- 单调函数的求根（如"最小化最大值"类问题）
- 旋转数组（局部有序）

## 三道经典题

---

### 题 1：二分查找（Binary Search）

**题目**：在有序数组中找 target，返回下标或 -1。

**思路**：维护搜索区间 `[left, right]`：
- `mid = left + (right - left) / 2`（防溢出）
- 如果 `nums[mid] == target`，返回 mid
- 如果 `nums[mid] < target`，`left = mid + 1`
- 如果 `nums[mid] > target`，`right = mid - 1`
- 循环条件 `left <= right`

**复杂度**：时间 O(log n)，空间 O(1)

**面试追问**：
- "为什么用 `left + (right - left) / 2` 而不是 `(left + right) / 2`？" → 防溢出
- "如果数组有重复元素，找第一个等于 target 的位置？" → 题 3

**破坏练习**：输入空数组、单元素数组、target 不在数组中

---

### 题 2：寻找旋转排序数组中的最小值（Find Minimum in Rotated Sorted Array）

**题目**：有序数组被旋转过（如 `[4,5,6,7,0,1,2]`），找最小值。

**思路**：二分查找，关键是比较 `nums[mid]` 和 `nums[right]`：
- 如果 `nums[mid] > nums[right]`，说明最小值在右半部分（`left = mid + 1`）
- 否则最小值在左半部分或就是 mid（`right = mid`）

**复杂度**：时间 O(log n)，空间 O(1)

**面试追问**：
- "如果有重复元素？" → `nums[mid] == nums[right]` 时 `right--`（退化为 O(n)）
- "找 target 而不是最小值？" → 先判断 mid 在哪一段（有序段还是旋转段），再决定搜索方向

**破坏练习**：数组没旋转（完全有序），观察算法是否仍正确

---

### 题 3：在排序数组中查找元素的第一个和最后一个位置（Find First and Last Position）

**题目**：找 target 在数组中的起始和结束下标，不存在返回 `[-1, -1]`。

**思路**：两次二分：
- **找左边界**：找第一个 `>= target` 的位置
- **找右边界**：找最后一个 `<= target` 的位置

**复杂度**：时间 O(log n)，空间 O(1)

**面试追问**：
- "为什么不能找到 target 后向两边扩展？" → 最坏 O(n)（全相同元素）
- "bisect_left 和 bisect_right 的区别？" → Python 标准库的实现

**破坏练习**：target 出现多次、target 不在数组中、数组全相同

---

## 代码实现

Java 和 Python 代码见对应目录，均含 main 函数可直接运行。

**运行方式**：
```bash
cd 07-binary-search
javac java/Solution.java && java -cp java Solution
# 或
python3 python/solution.py
```

## 二分的本质

所有二分题目的核心是**维护不变量**：
1. **确定搜索区间**：`[left, right]` 还是 `[left, right)`
2. **循环条件**：`left <= right` 还是 `left < right`
3. **更新策略**：`left = mid + 1` 还是 `left = mid`，`right = mid - 1` 还是 `right = mid`

面试时先说清这三点，再写代码，避免边界错误。
