# 数据库问答 (Databases Q&A)

## 核心概念

### 数据库类型概览

1. **关系型数据库 (RDBMS)**：MySQL, PostgreSQL, Oracle
2. **NoSQL 数据库**：
   - Document: MongoDB, CouchDB
   - Key-Value: Redis, DynamoDB
   - Column-family: Cassandra, HBase
   - Graph: Neo4j, Amazon Neptune

---

## 常见问题与回答

### 1. SQL vs NoSQL（SQL 与 NoSQL 对比）

#### 问题
```
What are the key differences between SQL and NoSQL databases? 
When would you choose one over the other?
```

#### 回答模板
```
SQL and NoSQL databases differ in several key aspects:

Schema:
- SQL: Fixed, predefined schema. All rows have the same structure.
- NoSQL: Flexible, dynamic schema. Documents can have different fields.

Scalability:
- SQL: Vertical scaling (bigger server). Harder to scale horizontally.
- NoSQL: Horizontal scaling (more servers). Designed for distributed systems.

Data Model:
- SQL: Relational model with tables, rows, and foreign keys.
- NoSQL: Various models (document, key-value, graph, column-family).

Transactions:
- SQL: ACID transactions (Atomicity, Consistency, Isolation, Durability).
- NoSQL: Often BASE (Basically Available, Soft state, Eventual consistency).

Query Language:
- SQL: Standardized SQL language, powerful joins and aggregations.
- NoSQL: Varies by database, often simpler queries, limited joins.

Choose SQL when:
- Data has clear structure and relationships
- ACID transactions are critical (e.g., financial systems)
- Complex queries with joins are needed
- Data integrity is paramount

Choose NoSQL when:
- Schema is evolving or varies by record
- Need to scale horizontally to handle massive data
- High write throughput is required
- Simple queries, no complex joins needed

In practice, many systems use both: SQL for transactional data, 
NoSQL for high-volume, flexible-schema data.
```

#### 关键表达
- **schema** - 模式/结构
- **vertical/horizontal scaling** - 垂直/水平扩展
- **ACID transactions** - ACID 事务
- **eventual consistency** - 最终一致性
- **BASE** - 基本可用、软状态、最终一致

---

### 2. Database Indexing（数据库索引）

#### 问题
```
What is a database index? How does it work and what are the trade-offs?
```

#### 回答模板
```
A database index is a data structure that improves the speed of data retrieval operations, 
similar to an index in a book.

How it works:
- Indexes are typically implemented as B-trees or hash tables
- B-tree indexes maintain sorted data, enabling efficient range queries
- The index stores key-value pairs: (indexed_column_value, row_pointer)
- When querying, the database traverses the index instead of scanning the entire table

Example:
```
Table: users (1 million rows)
Query: SELECT * FROM users WHERE email = 'alice@example.com'

Without index: Full table scan, O(n) = 1 million comparisons
With index on email: B-tree lookup, O(log n) ≈ 20 comparisons
```

Trade-offs:

Benefits:
- Faster SELECT queries (10x to 1000x improvement)
- Enable efficient range queries and sorting
- Enforce uniqueness constraints

Costs:
- Slower INSERT, UPDATE, DELETE (must update index)
- Additional storage space (typically 10-30% of table size)
- Memory usage for index caching

Best practices:
1. Index columns used in WHERE clauses
2. Index foreign keys for faster joins
3. Consider composite indexes for multi-column queries
4. Avoid over-indexing (diminishing returns)
5. Monitor index usage and remove unused indexes

Example of composite index:
```sql
-- Query: SELECT * FROM orders WHERE user_id = 123 AND status = 'shipped'
CREATE INDEX idx_user_status ON orders(user_id, status);
-- Column order matters: put most selective column first
```

In production, I always analyze query patterns and use EXPLAIN to verify 
that indexes are being used effectively.
```

#### 关键表达
- **B-tree** - B 树
- **full table scan** - 全表扫描
- **composite index** - 复合索引
- **query optimization** - 查询优化
- **EXPLAIN** - 执行计划分析

---

### 3. Database Normalization（数据库规范化）

#### 问题
```
What is database normalization? Explain the different normal forms.
```

#### 回答模板
```
Database normalization is the process of organizing data to reduce redundancy 
and improve data integrity.

The main normal forms are:

1NF (First Normal Form):
- Each column contains atomic values (no arrays or lists)
- Each row is unique (has a primary key)
- Example violation: phone_numbers column with "555-1234, 555-5678"

2NF (Second Normal Form):
- Meets 1NF
- No partial dependencies (all non-key columns depend on the entire primary key)
- Example violation: In a table with composite key (student_id, course_id), 
  if student_name depends only on student_id, it violates 2NF

3NF (Third Normal Form):
- Meets 2NF
- No transitive dependencies (non-key columns don't depend on other non-key columns)
- Example violation: If city depends on zip_code, and zip_code depends on address, 
  then city transitively depends on address

BCNF (Boyce-Codd Normal Form):
- Stronger version of 3NF
- Every determinant is a candidate key

Benefits of normalization:
- Reduced data redundancy (saves storage)
- Better data integrity (update in one place)
- Easier to maintain and modify schema

Trade-offs:
- More complex queries (need more joins)
- Potentially slower read performance
- May need to denormalize for performance

In practice:
- Start with normalized design (3NF)
- Denormalize selectively for performance-critical queries
- Use materialized views or caching to avoid expensive joins

Example of denormalization:
```
Normalized:
  orders table: order_id, user_id, total
  users table: user_id, name, email

Denormalized (for performance):
  orders table: order_id, user_id, user_name, user_email, total
  (Avoids join when displaying order details)
```
```

#### 关键表达
- **normalization** - 规范化
- **redundancy** - 冗余
- **data integrity** - 数据完整性
- **partial dependency** - 部分依赖
- **transitive dependency** - 传递依赖
- **denormalization** - 反规范化

---

### 4. Database Transactions（数据库事务）

#### 问题
```
What are ACID properties? Why are they important for database transactions?
```

#### 回答模板
```
ACID is a set of properties that guarantee reliable database transactions:

A - Atomicity (原子性):
- Transaction is all-or-nothing
- If any part fails, entire transaction is rolled back
- Example: Bank transfer - debit and credit must both succeed or both fail

C - Consistency (一致性):
- Database moves from one valid state to another
- All constraints and rules are maintained
- Example: Account balance cannot go negative if there's a constraint

I - Isolation (隔离性):
- Concurrent transactions don't interfere with each other
- Each transaction sees a consistent snapshot of the database
- Isolation levels: Read Uncommitted, Read Committed, Repeatable Read, Serializable

D - Durability (持久性):
- Once committed, transaction survives system failures
- Changes are permanently stored (typically in write-ahead log)
- Example: After commit, data survives power outage

Why ACID matters:
- Ensures data correctness in concurrent environments
- Critical for financial systems, e-commerce, inventory management
- Prevents race conditions and data corruption

Example - Bank transfer without ACID:
```
1. Read Alice's balance: $1000
2. Read Bob's balance: $500
3. Debit Alice: $1000 - $100 = $900
4. [SYSTEM CRASH]
5. Credit Bob: $500 + $100 = $600

Result: Alice lost $100, Bob didn't receive it!
With ACID: Transaction rolls back, no money lost
```

Trade-offs:
- Strict ACID can limit scalability and performance
- NoSQL databases often relax ACID for better performance (BASE)
- Choose consistency level based on business requirements

In distributed systems, achieving full ACID is challenging, 
so we often use patterns like Saga or two-phase commit.
```

#### 关键表达
- **ACID properties** - ACID 特性
- **atomicity** - 原子性
- **consistency** - 一致性
- **isolation** - 隔离性
- **durability** - 持久性
- **transaction rollback** - 事务回滚
- **race condition** - 竞态条件
- **write-ahead log** - 预写日志

---

### 5. Database Sharding（数据库分片）

#### 问题
```
What is database sharding? When and how would you implement it?
```

#### 回答模板
```
Database sharding is a horizontal scaling technique where data is partitioned 
across multiple database servers, called shards.

Why sharding:
- Single database server has limits (CPU, memory, disk, connections)
- Vertical scaling (bigger server) has diminishing returns and high cost
- Sharding distributes load across multiple machines

Sharding strategies:

1. Range-based sharding:
   - Partition by key ranges (e.g., user_id 1-1M → shard 1, 1M-2M → shard 2)
   - Pros: Simple, efficient range queries
   - Cons: Hot spots if data is not evenly distributed

2. Hash-based sharding:
   - Hash the shard key and use modulo (e.g., hash(user_id) % 16)
   - Pros: Even distribution, no hot spots
   - Cons: Range queries require querying all shards

3. Directory-based sharding:
   - Lookup table maps keys to shards
   - Pros: Flexible, can move data between shards
   - Cons: Lookup table is a single point of failure

Challenges:
1. Cross-shard queries
   - Query must be sent to multiple shards and results merged
   - Solution: Denormalize data or use a separate analytics database

2. Distributed transactions
   - ACID across shards is complex
   - Solution: Saga pattern, two-phase commit, or eventual consistency

3. Resharding
   - Adding or removing shards requires data migration
   - Solution: Consistent hashing minimizes data movement

4. Shard key selection
   - Must be in most queries to avoid cross-shard operations
   - Should distribute data evenly

Example architecture:
```
Application
    ↓
Shard Router (determines which shard to query)
    ↓
┌─────────┬─────────┬─────────┐
│ Shard 1 │ Shard 2 │ Shard 3 │
│ user    │ user    │ user    │
│ 1-1000  │ 1001-   │ 2001-   │
│         │ 2000    │ 3000    │
└─────────┴─────────┴─────────┘
```

When to shard:
- Single database can't handle the load (> 10K queries/second)
- Dataset exceeds single server's storage capacity
- Need geographic distribution for low latency

When NOT to shard:
- Can solve performance issues with indexing, caching, or read replicas
- Application doesn't need horizontal scaling yet
- Complexity cost outweighs benefits
```

#### 关键表达
- **sharding** - 分片
- **horizontal scaling** - 水平扩展
- **shard key** - 分片键
- **cross-shard query** - 跨分片查询
- **resharding** - 重新分片
- **consistent hashing** - 一致性哈希
- **hot spot** - 热点

---

### 6. Database Replication（数据库复制）

#### 问题
```
What is database replication? What are the different replication strategies?
```

#### 回答模板
```
Database replication is the process of copying data from one database (primary/master) 
to one or more databases (replicas/slaves) to improve availability and read performance.

Why replication:
- High availability: If primary fails, promote a replica
- Read scalability: Distribute read queries across replicas
- Disaster recovery: Maintain copies in different data centers
- Analytics: Run heavy queries on replicas without affecting production

Replication strategies:

1. Primary-Replica (Master-Slave):
   - One primary handles all writes
   - Multiple replicas handle reads
   - Replication is asynchronous (eventual consistency)
   - Pros: Simple, good read scalability
   - Cons: Replication lag, replica may be stale

2. Multi-Primary (Master-Master):
   - Multiple primaries accept writes
   - Changes replicated to all nodes
   - Pros: High write availability
   - Cons: Conflict resolution needed, complex

3. Synchronous vs Asynchronous:
   - Synchronous: Primary waits for replica acknowledgment
     - Pros: Strong consistency, no data loss
     - Cons: Higher latency, lower availability
   - Asynchronous: Primary doesn't wait
     - Pros: Lower latency, higher availability
     - Cons: Potential data loss if primary fails

Replication lag:
- Time delay between write on primary and visibility on replica
- Typical lag: milliseconds to seconds
- Can cause consistency issues (read-your-writes problem)
- Solutions: 
  * Read from primary for critical data
  * Use semi-synchronous replication
  * Application-level retry logic

Example setup:
```
Primary (handles writes)
    ↓ (replication)
┌─────────┬─────────┬─────────┐
│Replica 1│Replica 2│Replica 3│
│(reads)  │(reads)  │(reads)  │
└─────────┴─────────┴─────────┘
    ↓
Load Balancer (routes reads to replicas)
```

Best practices:
1. Monitor replication lag
2. Use read replicas for analytics and reporting
3. Implement retry logic for read-your-writes scenarios
4. Have automated failover to promote replica if primary fails
5. Test failover procedures regularly

In production, I typically use primary-replica with asynchronous replication, 
and read from primary when consistency is critical.
```

#### 关键表达
- **replication** - 复制
- **primary/replica (master/slave)** - 主/从
- **replication lag** - 复制延迟
- **eventual consistency** - 最终一致性
- **failover** - 故障转移
- **read-your-writes** - 读己之所写

---

## 实践问题

### 7. Query Optimization（查询优化）

#### 问题
```
How do you approach optimizing a slow database query?
```

#### 回答模板
```
Optimizing a slow query is a systematic process:

Step 1: Identify the slow query
- Use slow query log (MySQL: slow_query_log)
- Monitor query execution times
- Profile application to find database bottlenecks

Step 2: Analyze the execution plan
```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 123 AND status = 'shipped';
```
- Look for full table scans (should use index)
- Check join types (nested loop vs hash join)
- Identify expensive operations (sort, group by)

Step 3: Optimize based on findings

Common optimizations:

1. Add appropriate indexes:
```sql
-- If WHERE clause uses user_id and status frequently
CREATE INDEX idx_user_status ON orders(user_id, status);
```

2. Rewrite the query:
```sql
-- Instead of SELECT *, select only needed columns
SELECT order_id, total, created_at 
FROM orders 
WHERE user_id = 123 AND status = 'shipped';
```

3. Optimize joins:
```sql
-- Denormalize frequently joined data
-- Or use materialized views for complex joins
```

4. Partition large tables:
```sql
-- Partition by date for time-series data
CREATE TABLE orders (
    ...
) PARTITION BY RANGE (YEAR(created_at));
```

5. Use query hints (sparingly):
```sql
-- Force use of specific index
SELECT * FROM orders USE INDEX (idx_user_status) 
WHERE user_id = 123;
```

Step 4: Verify the improvement
- Run EXPLAIN again to confirm index usage
- Measure execution time before and after
- Monitor in production to ensure sustained improvement

Step 5: Consider architectural changes if needed
- Add caching layer (Redis) for frequent queries
- Use read replicas to distribute read load
- Denormalize data to avoid expensive joins
- Consider sharding if dataset is too large

Real-world example:
I once optimized a query that took 30 seconds down to 50ms:
- Problem: Full table scan on 10 million rows
- Solution: Added composite index on (user_id, created_at)
- Result: Query used index, execution time dropped 600x

The key is to always measure and verify that optimizations actually help.
```

#### 关键表达
- **execution plan** - 执行计划
- **full table scan** - 全表扫描
- **query profiling** - 查询分析
- **index hint** - 索引提示
- **materialized view** - 物化视图

---

## 数据库选择指南

### When to use which database?

| Use Case | Recommended Database | Reason |
|----------|---------------------|--------|
| E-commerce transactions | PostgreSQL, MySQL | ACID, complex queries |
| Social media feed | Cassandra, DynamoDB | High write throughput, horizontal scale |
| Real-time analytics | ClickHouse, Druid | Columnar storage, fast aggregations |
| Content management | MongoDB | Flexible schema, document model |
| Caching | Redis, Memcached | In-memory, low latency |
| Time series data | InfluxDB, TimescaleDB | Optimized for time-based queries |
| Graph relationships | Neo4j, Neptune | Native graph storage and queries |
| Session storage | Redis | Fast key-value, TTL support |

---

## 学习资源

- **书籍**：《Designing Data-Intensive Applications》by Martin Kleppmann
- **课程**：CMU Database Group (YouTube)
- **实践**：Set up your own database cluster, experiment with replication and sharding
- **工具**：Use EXPLAIN extensively, learn to read execution plans
