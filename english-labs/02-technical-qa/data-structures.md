# 数据结构问答 (Data Structures Q&A)

## 核心概念

### 为什么数据结构重要？

数据结构是面试必考内容，因为：
- 展示你对计算机科学的理解深度
- 体现你的问题解决能力
- 直接影响代码性能（时间/空间复杂度）

### 回答框架

```
1. Definition - 定义数据结构
2. Use cases - 适用场景
3. Operations - 核心操作及复杂度
4. Implementation - 实现细节（如需要）
5. Trade-offs - 优缺点对比
6. Real-world examples - 实际应用
```

---

## 基础数据结构

### 1. Arrays vs Linked Lists（数组 vs 链表）

#### 问题
```
What are the differences between arrays and linked lists? 
When would you choose one over the other?
```

#### 回答模板
```
Arrays and linked lists are both linear data structures, but they have different characteristics.

Arrays:
- Store elements in contiguous memory locations
- Provide O(1) random access by index
- Have fixed size (in most languages)
- Insertion and deletion are O(n) in the worst case

Linked Lists:
- Store elements in non-contiguous memory, connected by pointers
- Provide O(n) access (need to traverse from head)
- Dynamic size, can grow or shrink
- Insertion and deletion are O(1) if you have the pointer

I would choose arrays when:
- I need fast random access
- The size is known and fixed
- Memory efficiency is important (no pointer overhead)

I would choose linked lists when:
- I need frequent insertions and deletions
- The size is dynamic and unpredictable
- I'm implementing other data structures like queues or stacks

In practice, arrays are often preferred due to better cache locality, 
unless we specifically need the dynamic nature of linked lists.
```

#### 关键表达
- **contiguous memory locations** - 连续内存位置
- **random access** - 随机访问
- **pointer overhead** - 指针开销
- **cache locality** - 缓存局部性
- **dynamic size** - 动态大小

---

### 2. Stacks and Queues（栈和队列）

#### 问题
```
Explain the difference between stacks and queues. 
Give examples of when you would use each.
```

#### 回答模板
```
Stacks and queues are both abstract data types that differ in how elements are added and removed.

Stack follows LIFO (Last In, First Out) principle:
- push() adds an element to the top - O(1)
- pop() removes the top element - O(1)
- peek() returns the top element without removing - O(1)

Queue follows FIFO (First In, First Out) principle:
- enqueue() adds an element to the back - O(1)
- dequeue() removes the front element - O(1)
- front() returns the front element without removing - O(1)

Use cases for stacks:
- Function call stack in programming languages
- Undo/redo operations in editors
- Expression evaluation and parsing
- Browser back button

Use cases for queues:
- Task scheduling in operating systems
- Print job queues
- BFS (Breadth-First Search) in graph algorithms
- Message queues in distributed systems

The choice depends on whether you need LIFO or FIFO behavior for your specific use case.
```

#### 关键表达
- **LIFO (Last In, First Out)** - 后进先出
- **FIFO (First In, First Out)** - 先进先出
- **abstract data types** - 抽象数据类型
- **function call stack** - 函数调用栈
- **BFS (Breadth-First Search)** - 广度优先搜索

---

### 3. Hash Tables（哈希表）

#### 问题
```
How does a hash table work? What are hash collisions and how do you handle them?
```

#### 回答模板
```
A hash table is a data structure that provides O(1) average time complexity for 
insertion, deletion, and lookup operations.

How it works:
1. A hash function converts the key into an array index
2. The value is stored at that index
3. To retrieve, we hash the key again and go directly to that index

Hash collisions occur when two different keys hash to the same index. 
There are two main strategies to handle collisions:

1. Chaining (Separate Chaining):
   - Each bucket contains a linked list of entries
   - Colliding entries are added to the same list
   - Lookup time becomes O(k) where k is the list length
   - Used in Java's HashMap

2. Open Addressing:
   - All entries are stored in the hash table itself
   - When collision occurs, find the next available slot
   - Methods: linear probing, quadratic probing, double hashing
   - Used in Python's dict

Performance considerations:
- Load factor = number of entries / table size
- When load factor exceeds threshold (usually 0.75), resize the table
- Resizing involves rehashing all entries, which is O(n)
- Good hash functions distribute keys uniformly

Real-world applications:
- Database indexing
- Caching systems
- Symbol tables in compilers
- Sets and dictionaries in programming languages
```

#### 关键表达
- **hash function** - 哈希函数
- **hash collisions** - 哈希冲突
- **chaining** - 链地址法
- **open addressing** - 开放寻址法
- **load factor** - 负载因子
- **linear probing** - 线性探测
- **rehashing** - 重新哈希

---

### 4. Trees（树）

#### 问题
```
What is a binary search tree? What are its properties and limitations?
```

#### 回答模板
```
A binary search tree (BST) is a binary tree where each node has at most two children, 
and for each node:
- All values in the left subtree are less than the node's value
- All values in the right subtree are greater than the node's value

This property enables efficient operations:
- Search: O(log n) average, O(n) worst case
- Insertion: O(log n) average, O(n) worst case
- Deletion: O(log n) average, O(n) worst case
- In-order traversal gives sorted sequence

The limitation of BST is that it can become unbalanced:
- If we insert sorted data, it degenerates into a linked list
- Operations degrade to O(n) in the worst case

To solve this, we use balanced BSTs:
- AVL Tree: maintains balance by ensuring height difference ≤ 1
- Red-Black Tree: uses color properties to maintain approximate balance
- B-Tree: allows multiple keys per node, used in databases

Applications:
- Database indexing (B-Trees, B+ Trees)
- File systems (directory structures)
- Expression parsing (abstract syntax trees)
- Priority queues (heaps are complete binary trees)
- Autocomplete and spell checking (Trie trees)

In practice, most standard libraries use balanced trees:
- Java's TreeMap uses Red-Black Tree
- C++'s std::map uses Red-Black Tree
- PostgreSQL uses B+ Trees for indexing
```

#### 关键表达
- **binary search tree (BST)** - 二叉搜索树
- **left subtree / right subtree** - 左子树 / 右子树
- **in-order traversal** - 中序遍历
- **balanced tree** - 平衡树
- **AVL Tree** - AVL 树
- **Red-Black Tree** - 红黑树
- **B-Tree / B+ Tree** - B 树 / B+ 树
- **degenerate into a linked list** - 退化为链表

---

### 5. Heaps（堆）

#### 问题
```
What is a heap? How is it different from a binary search tree? When would you use a heap?
```

#### 回答模板
```
A heap is a specialized tree-based data structure that satisfies the heap property:
- Max Heap: parent node is greater than or equal to its children
- Min Heap: parent node is less than or equal to its children

Key characteristics:
- Complete binary tree (all levels filled except possibly the last)
- Usually implemented as an array for efficiency
- Does NOT maintain sorted order (unlike BST)
- Root is always the max (max heap) or min (min heap)

Key operations:
- insert(): O(log n) - add element and bubble up
- extractMax/Min(): O(log n) - remove root and bubble down
- peek(): O(1) - return root without removing
- buildHeap(): O(n) - construct heap from array

Differences from BST:
- BST maintains sorted order, heap only maintains heap property
- BST supports efficient search for any element, heap only for min/max
- BST can be unbalanced, heap is always balanced (complete tree)
- Heap has better constant factors for priority queue operations

Use cases for heaps:
1. Priority queues - task scheduling, event processing
2. Top-K problems - finding K largest/smallest elements
3. Heap sort - O(n log n) sorting algorithm
4. Graph algorithms - Dijkstra's, Prim's minimum spanning tree
5. Median maintenance - using two heaps (max heap + min heap)

Example: Finding top K elements
```python
import heapq

def top_k(numbers, k):
    # Use min heap of size k
    return heapq.nlargest(k, numbers)
```

This is more efficient than sorting the entire array when k << n.
```

#### 关键表达
- **heap property** - 堆性质
- **max heap / min heap** - 最大堆 / 最小堆
- **complete binary tree** - 完全二叉树
- **bubble up / bubble down** - 上浮 / 下沉
- **priority queue** - 优先队列
- **Top-K problem** - Top-K 问题

---

### 6. Graphs（图）

#### 问题
```
How do you represent a graph? What are the trade-offs between different representations?
```

#### 回答模板
```
There are two main ways to represent a graph:

1. Adjacency Matrix:
   - 2D array where matrix[i][j] represents edge from i to j
   - For weighted graphs, store the weight instead of 1/0
   - Space: O(V²) where V is number of vertices
   - Edge lookup: O(1)
   - Finding neighbors: O(V)

2. Adjacency List:
   - Array of lists, where list[i] contains all neighbors of vertex i
   - For weighted graphs, store (neighbor, weight) pairs
   - Space: O(V + E) where E is number of edges
   - Edge lookup: O(degree)
   - Finding neighbors: O(degree)

Trade-offs:
- Adjacency matrix is better for:
  * Dense graphs (E ≈ V²)
  * Frequent edge lookups
  * Small graphs (memory not a concern)

- Adjacency list is better for:
  * Sparse graphs (E << V²)
  * Iterating over neighbors
  * Large graphs (memory efficient)

In practice, adjacency list is more commonly used because most real-world graphs are sparse.

Graph traversal algorithms:
- BFS (Breadth-First Search): uses queue, finds shortest path in unweighted graphs
- DFS (Depth-First Search): uses stack/recursion, good for path finding and cycle detection

Applications:
- Social networks (friend recommendations)
- Maps and navigation (shortest path)
- Web crawlers (page rank)
- Dependency resolution (topological sort)
- Network routing protocols
```

#### 关键表达
- **adjacency matrix** - 邻接矩阵
- **adjacency list** - 邻接表
- **dense graph / sparse graph** - 稠密图 / 稀疏图
- **BFS (Breadth-First Search)** - 广度优先搜索
- **DFS (Depth-First Search)** - 深度优先搜索
- **topological sort** - 拓扑排序
- **shortest path** - 最短路径

---

## 高级数据结构

### 7. Trie（字典树）

#### 问题
```
What is a Trie? When would you use it over a hash table?
```

#### 回答模板
```
A Trie (pronounced "try") is a tree-like data structure used for efficient retrieval 
of keys in a dataset of strings.

Structure:
- Each node represents a character
- Path from root to node represents a prefix
- Leaf nodes or marked nodes represent complete words
- Children are typically stored in an array or hash map

Operations:
- Insert: O(m) where m is word length
- Search: O(m)
- Prefix search: O(m + k) where k is number of matches

Advantages over hash tables:
1. Prefix matching - find all words with given prefix efficiently
2. Ordered iteration - traverse in lexicographical order
3. No hash collisions - deterministic performance
4. Space efficient for common prefixes - shared paths

Disadvantages:
1. More memory for sparse datasets
2. Slower than hash tables for exact lookups (due to pointer chasing)
3. Not suitable for non-string keys

Applications:
- Autocomplete systems
- Spell checkers
- IP routing (longest prefix matching)
- Dictionary implementations
- Search engines (query suggestions)

Example: Autocomplete
```python
class Trie:
    def __init__(self):
        self.children = {}
        self.is_word = False
    
    def insert(self, word):
        node = self
        for char in word:
            if char not in node.children:
                node.children[char] = Trie()
            node = node.children[char]
        node.is_word = True
    
    def find_prefix(self, prefix):
        node = self
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        # DFS to find all words with this prefix
        return self._get_all_words(node, prefix)
```

For production autocomplete, you'd also store frequency/popularity scores 
to rank suggestions.
```

#### 关键表达
- **prefix matching** - 前缀匹配
- **lexicographical order** - 字典序
- **autocomplete** - 自动补全
- **spell checker** - 拼写检查器
- **longest prefix matching** - 最长前缀匹配

---

### 8. Bloom Filter（布隆过滤器）

#### 问题
```
What is a Bloom filter? What are its use cases and limitations?
```

#### 回答模板
```
A Bloom filter is a space-efficient probabilistic data structure used to test 
whether an element is a member of a set.

How it works:
- Uses a bit array and multiple hash functions
- To insert: hash the element with k hash functions, set those bits to 1
- To query: hash the element, check if all k bits are 1
- If any bit is 0, element is definitely NOT in the set
- If all bits are 1, element is PROBABLY in the set (may be false positive)

Key properties:
- No false negatives (if it says not present, it's definitely not)
- Possible false positives (if it says present, might not be)
- Cannot delete elements (without modifications like Counting Bloom Filter)
- Space efficient: much smaller than storing actual elements

Parameters:
- m: size of bit array
- k: number of hash functions
- n: number of elements inserted
- False positive rate: (1 - e^(-kn/m))^k

Use cases:
1. Database query optimization
   - Check if record exists before expensive disk lookup
   - Reduces disk I/O for non-existent keys

2. Web crawlers
   - Track visited URLs to avoid revisiting
   - Saves memory compared to storing all URLs

3. Spell checkers
   - Quick check if word might be valid
   - Then do expensive dictionary lookup only if needed

4. Distributed systems
   - Check if data exists on a node before network request
   - Reduces unnecessary network traffic

5. Cache filtering
   - Decide whether to cache an item
   - Avoid caching one-time queries (cache pollution)

Example: Database optimization
```
Before querying disk:
if bloom_filter.might_contain(key):
    # Might be in database, do expensive disk lookup
    result = disk_lookup(key)
else:
    # Definitely not in database, skip disk lookup
    return None
```

Limitations:
- Cannot enumerate all elements
- Cannot delete elements (standard version)
- False positive rate increases with more elements
- Not suitable when false positives are unacceptable
```

#### 关键表达
- **probabilistic data structure** - 概率数据结构
- **false positive / false negative** - 假阳性 / 假阴性
- **bit array** - 位数组
- **hash functions** - 哈希函数
- **space efficient** - 空间高效
- **cache pollution** - 缓存污染

---

## 复杂度对比表

| Data Structure | Insert | Delete | Search | Space |
|----------------|--------|--------|--------|-------|
| Array (unsorted) | O(1) | O(n) | O(n) | O(n) |
| Array (sorted) | O(n) | O(n) | O(log n) | O(n) |
| Linked List | O(1) | O(n) | O(n) | O(n) |
| Hash Table | O(1)* | O(1)* | O(1)* | O(n) |
| BST (balanced) | O(log n) | O(log n) | O(log n) | O(n) |
| BST (unbalanced) | O(n) | O(n) | O(n) | O(n) |
| Heap | O(log n) | O(log n) | O(n) | O(n) |
| Trie | O(m) | O(m) | O(m) | O(ALPHABET_SIZE × m × n) |

*Average case, worst case is O(n) for hash table

---

## 练习建议

1. **理解而非记忆**：理解每个数据结构的原理和适用场景
2. **手写实现**：至少实现一次基础版本
3. **复杂度分析**：能够分析每个操作的时间/空间复杂度
4. **对比学习**：比较相似数据结构的优缺点
5. **实际应用**：思考在真实项目中如何使用

## 推荐资源

- **书籍**：《Introduction to Algorithms》(CLRS)
- **视频**：MIT 6.006 Introduction to Algorithms
- **练习**：LeetCode Data Structures 标签
- **可视化**：VisuAlgo (https://visualgo.net)
