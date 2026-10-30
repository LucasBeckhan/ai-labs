# 分布式系统问答 (Distributed Systems Q&A)

## 核心概念

### 为什么需要分布式系统？

1. **Scalability（可扩展性）**：单台机器有性能上限
2. **Reliability（可靠性）**：避免单点故障
3. **Performance（性能）**：就近服务用户，减少延迟
4. **Cost（成本）**：多台廉价机器 vs 单台昂贵机器

---

## 基础理论

### 1. CAP Theorem（CAP 定理）

#### 问题
```
What is the CAP theorem? How does it affect system design decisions?
```

#### 回答模板
```
The CAP theorem states that a distributed system can only guarantee two of three 
properties at the same time:

C - Consistency (一致性):
- All nodes see the same data at the same time
- After a write, all subsequent reads return the updated value
- Example: Bank transfer - both accounts must show updated balance immediately

A - Availability (可用性):
- Every request receives a response (success or failure)
- System remains operational even if some nodes fail
- Example: Social media feed - better to show slightly stale data than error

P - Partition Tolerance (分区容错性):
- System continues to operate despite network partitions
- Network failures between nodes don't crash the system
- In practice, this is mandatory for distributed systems

The theorem says: In the presence of a network partition (P), 
you must choose between consistency (C) and availability (A).

CP systems (Consistency + Partition tolerance):
- Choose consistency over availability
- During network partition, some requests may fail or timeout
- Examples: ZooKeeper, HBase, MongoDB (with strong consistency)
- Use case: Financial transactions, inventory management

AP systems (Availability + Partition tolerance):
- Choose availability over consistency
- During network partition, system continues but may return stale data
- Examples: Cassandra, DynamoDB, CouchDB
- Use case: Social media, recommendation systems, caching

CA systems (Consistency + Availability):
- Only possible in single-node systems (no partitions)
- Examples: Traditional RDBMS on single server
- Not truly distributed

In practice:
- Network partitions are inevitable in distributed systems
- So the real choice is between CP and AP
- Many systems allow tuning consistency level per operation
- Example: Cassandra allows choosing consistency level (ONE, QUORUM, ALL)

Real-world example:
For an e-commerce platform:
- Inventory system: CP (can't oversell products)
- Product reviews: AP (okay if review appears with delay)
- Shopping cart: AP (better to allow adding items than reject)
- Payment processing: CP (must be consistent)

The key is to understand your application's requirements and choose 
the appropriate consistency model for each component.
```

#### 关键表达
- **CAP theorem** - CAP 定理
- **network partition** - 网络分区
- **consistency model** - 一致性模型
- **trade-off** - 权衡
- **eventual consistency** - 最终一致性

---

### 2. Consistency Models（一致性模型）

#### 问题
```
What are the different consistency models in distributed systems?
```

#### 回答模板
```
Consistency models define the guarantees a system provides about how and when 
updates become visible to readers.

Strong Consistency Models:

1. Linearizability (Strong Consistency):
   - All operations appear to execute atomically in some total order
   - Once a write completes, all subsequent reads see the new value
   - Most intuitive but hardest to achieve
   - Example: ZooKeeper, etcd

2. Sequential Consistency:
   - All operations appear to execute in some sequential order
   - Each process's operations appear in program order
   - Weaker than linearizability (no real-time ordering)
   - Example: Some distributed locks

Weak Consistency Models:

3. Eventual Consistency:
   - If no new updates, all replicas eventually converge
   - Reads may return stale data temporarily
   - Most common in AP systems
   - Example: DNS, Cassandra (default), DynamoDB

4. Causal Consistency:
   - Causally related operations are seen in order by all processes
   - Unrelated operations may be seen in different orders
   - Stronger than eventual, weaker than sequential
   - Example: Some social media systems

5. Read-your-writes Consistency:
   - A process always sees its own writes
   - May not see other processes' recent writes
   - Important for user experience
   - Example: User updates profile, immediately sees the change

6. Monotonic Reads:
   - If a process reads a value, it never sees older values later
   - Prevents "time travel" in reads
   - Example: Reading news feed shouldn't show older posts after newer ones

Consistency spectrum (strongest to weakest):
Linearizability > Sequential > Causal > Read-your-writes > Eventual

Choosing the right model:

Use strong consistency when:
- Data correctness is critical (financial transactions)
- Users expect immediate consistency (inventory counts)
- System can tolerate higher latency

Use eventual consistency when:
- High availability is more important than immediate consistency
- Temporary inconsistency is acceptable (social media likes)
- Need to scale to massive write throughput

In practice, many systems use different consistency levels for different operations:
- Writes: Strong consistency for critical data
- Reads: Eventual consistency for better performance
- Specific operations: Read-your-writes for user experience

Example - E-commerce system:
- Product inventory: Strong consistency (prevent overselling)
- Product reviews: Eventual consistency (delay is acceptable)
- User session: Read-your-writes (user sees their own changes)
- Recommendation: Eventual consistency (stale is okay)

The key is to understand the business requirements and choose 
the weakest consistency model that satisfies them, as stronger 
consistency comes with higher cost and lower availability.
```

#### 关键表达
- **consistency model** - 一致性模型
- **linearizability** - 线性一致性
- **sequential consistency** - 顺序一致性
- **eventual consistency** - 最终一致性
- **causal consistency** - 因果一致性
- **read-your-writes** - 读己之所写
- **stale data** - 陈旧数据

---

### 3. Distributed Consensus（分布式共识）

#### 问题
```
What is distributed consensus? Explain Paxos or Raft.
```

#### 回答模板
```
Distributed consensus is the problem of getting multiple nodes in a distributed system 
to agree on a single value or decision, even in the presence of failures.

Why consensus is important:
- Leader election: Which node is the primary?
- State machine replication: Keep replicas in sync
- Configuration management: Agree on system configuration
- Distributed transactions: Commit or abort across nodes

The challenge:
- Nodes can fail (crash, network partition)
- Messages can be lost, delayed, or reordered
- Need to reach agreement despite these failures

Raft Algorithm (simpler alternative to Paxos):

Raft breaks consensus into three subproblems:

1. Leader Election:
   - One node is elected as leader
   - Leader handles all client requests
   - Followers replicate leader's log
   - If leader fails, followers elect new leader

   Election process:
   - Candidates request votes from other nodes
   - Need majority (N/2 + 1) to win
   - Randomized timeouts prevent split votes

2. Log Replication:
   - Leader receives client requests
   - Appends to local log
   - Replicates to followers via AppendEntries RPC
   - Commits when majority acknowledge
   - Followers apply committed entries to state machine

3. Safety:
   - Election Restriction: Only nodes with up-to-date logs can become leader
   - Log Matching: If two logs have same index and term, they're identical
   - Leader Completeness: Committed entries are present on all future leaders

Example - Leader election:
```
Initial state: All nodes are followers
Node 1: Timeout, becomes candidate, requests votes
Node 2, 3: Grant votes (Node 1 has up-to-date log)
Node 1: Wins election (2 out of 3 votes), becomes leader
Node 2, 3: Become followers

If Node 1 fails:
Node 2: Timeout, becomes candidate
Node 3: Grants vote
Node 2: Wins election, becomes new leader
```

Raft vs Paxos:
- Raft is designed for understandability
- Paxos is more efficient but harder to understand
- Both provide same guarantees (safety and liveness)
- Raft is more commonly used in practice

Real-world implementations:
- etcd: Uses Raft, used by Kubernetes for configuration
- Consul: Uses Raft for consistency
- ZooKeeper: Uses Zab (similar to Raft)
- CockroachDB: Uses Raft for replication

In my experience with Kubernetes:
- etcd uses Raft for consensus
- All cluster state stored in etcd
- API server reads from etcd, writes go through etcd
- If etcd loses quorum, cluster becomes read-only

The key insight is that consensus protocols allow us to build 
reliable distributed systems despite individual node failures, 
which is fundamental to modern cloud infrastructure.
```

#### 关键表达
- **distributed consensus** - 分布式共识
- **leader election** - 领导者选举
- **log replication** - 日志复制
- **state machine** - 状态机
- **quorum** - 法定人数（多数派）
- **split brain** - 脑裂

---

## 实践问题

### 4. Distributed Transactions（分布式事务）

#### 问题
```
How do you handle transactions across multiple services in a microservices architecture?
```

#### 回答模板
```
Distributed transactions across microservices are challenging because we can't use 
traditional ACID transactions. There are several patterns to handle this:

1. Two-Phase Commit (2PC):
   - Coordinator asks all participants to prepare (Phase 1)
   - If all agree, coordinator sends commit (Phase 2)
   - If any fails, coordinator sends rollback
   
   Pros: Strong consistency
   Cons: Blocking protocol, coordinator is single point of failure, 
         poor performance, not suitable for microservices

2. Saga Pattern:
   - Break transaction into a sequence of local transactions
   - Each local transaction has a compensating transaction
   - If a step fails, execute compensating transactions in reverse order
   
   Example - Order processing:
   ```
   1. Create order (compensate: cancel order)
   2. Reserve inventory (compensate: release inventory)
   3. Process payment (compensate: refund payment)
   4. Ship order (compensate: return shipment)
   
   If payment fails:
   - Release inventory (compensate step 2)
   - Cancel order (compensate step 1)
   ```
   
   Two implementation styles:
   - Choreography: Each service publishes events, others react
   - Orchestration: Central coordinator directs the flow
   
   Pros: No global lock, better performance
   Cons: Eventual consistency, complex compensation logic

3. Event Sourcing:
   - Store state changes as sequence of events
   - Reconstruct current state by replaying events
   - Enables temporal queries and audit trail
   
   Example:
   ```
   Events:
   - OrderCreated(orderId, userId, items)
   - PaymentReceived(orderId, amount)
   - OrderShipped(orderId, trackingNumber)
   
   Current state derived from events
   ```

4. CQRS (Command Query Responsibility Segregation):
   - Separate read and write models
   - Write commands update event store
   - Read queries use denormalized views
   
   Benefits:
   - Optimize read and write independently
   - Eventual consistency between read and write
   - Better scalability

In practice, I use Saga pattern for most microservices transactions:

Example - E-commerce checkout:
```
Orchestrator Service:
1. Call Order Service: Create order
2. Call Inventory Service: Reserve items
3. Call Payment Service: Process payment
4. Call Shipping Service: Create shipment

If step 3 fails:
- Call Inventory Service: Release items (compensate step 2)
- Call Order Service: Cancel order (compensate step 1)
- Return failure to user
```

Key considerations:
- Idempotency: Operations must be safe to retry
- Compensation: Must handle partial failures gracefully
- Monitoring: Track saga progress and failures
- Recovery: Handle system crashes during saga execution

Best practices:
1. Design for failure from the start
2. Make operations idempotent
3. Use event-driven architecture where possible
4. Implement proper error handling and compensation
5. Log all saga steps for debugging and recovery

The key insight is that in distributed systems, we trade strong consistency 
for availability and partition tolerance, and use patterns like Saga to 
manage the resulting complexity.
```

#### 关键表达
- **distributed transaction** - 分布式事务
- **two-phase commit (2PC)** - 两阶段提交
- **Saga pattern** - Saga 模式
- **compensating transaction** - 补偿事务
- **event sourcing** - 事件溯源
- **CQRS** - 命令查询职责分离
- **idempotency** - 幂等性
- **choreography / orchestration** - 编排 / 协调

---

### 5. Load Balancing（负载均衡）

#### 问题
```
What are the different load balancing strategies? When would you use each?
```

#### 回答模板
```
Load balancing distributes incoming requests across multiple servers to improve 
performance and reliability.

Load Balancing Algorithms:

1. Round Robin:
   - Distribute requests sequentially across servers
   - Pros: Simple, fair distribution
   - Cons: Doesn't consider server load or capacity
   - Use case: Homogeneous servers, simple workloads

2. Weighted Round Robin:
   - Assign weights to servers based on capacity
   - Server with weight 2 gets twice as many requests as weight 1
   - Pros: Handles heterogeneous servers
   - Cons: Still doesn't consider current load
   - Use case: Servers with different capacities

3. Least Connections:
   - Send request to server with fewest active connections
   - Pros: Adapts to current load
   - Cons: Connections may have different durations
   - Use case: Long-lived connections (WebSocket, database)

4. Least Response Time:
   - Send to server with fastest response time
   - Pros: Optimizes for user experience
   - Cons: Requires monitoring, can cause oscillation
   - Use case: Latency-sensitive applications

5. IP Hash:
   - Hash client IP to select server
   - Same client always goes to same server
   - Pros: Session affinity without cookies
   - Cons: Uneven distribution if IPs not uniform
   - Use case: Session-based applications

6. Consistent Hashing:
   - Hash both requests and servers to a ring
   - Each server handles a range of the hash space
   - When server added/removed, only affected keys move
   - Pros: Minimal redistribution, good for caching
   - Cons: More complex
   - Use case: Distributed caches, sharded databases

Load Balancer Types:

1. Layer 4 (Transport Layer):
   - Operates at TCP/UDP level
   - Makes routing decisions based on IP and port
   - Faster, less intelligent
   - Examples: HAProxy (TCP mode), AWS NLB

2. Layer 7 (Application Layer):
   - Operates at HTTP/HTTPS level
   - Can inspect headers, cookies, URL paths
   - More intelligent routing (path-based, header-based)
   - Examples: Nginx, HAProxy (HTTP mode), AWS ALB

3. DNS Load Balancing:
   - Return multiple IP addresses for a domain
   - Client chooses which IP to connect to
   - Simple but limited control
   - Examples: Route 53, CloudFlare

Health Checks:
- Load balancer periodically checks server health
- Remove unhealthy servers from rotation
- Add back when healthy again
- Methods: HTTP GET, TCP connect, custom scripts

Example - Multi-tier architecture:
```
Internet
    ↓
DNS Load Balancing (Route 53)
    ↓
Layer 7 Load Balancer (Nginx)
    ↓ (path-based routing)
┌────────────────┬────────────────┐
│ API Servers    │ Static Content │
│ (Least Conn)   │ (Round Robin)  │
└────────────────┴────────────────┘
    ↓
Layer 4 Load Balancer (HAProxy TCP)
    ↓
Database Cluster (Primary-Replica)
```

In production, I typically use:
- Layer 7 LB for web traffic (Nginx or ALB)
- Least connections for API servers
- Consistent hashing for caching layers
- Health checks with 30-second interval, 3 failures to mark down

The key is to choose the right algorithm based on your workload characteristics 
and use multiple layers of load balancing for complex architectures.
```

#### 关键表达
- **load balancing** - 负载均衡
- **round robin** - 轮询
- **weighted round robin** - 加权轮询
- **least connections** - 最少连接
- **consistent hashing** - 一致性哈希
- **Layer 4 / Layer 7** - 四层 / 七层
- **health check** - 健康检查
- **session affinity** - 会话亲和性

---

### 6. Message Queues（消息队列）

#### 问题
```
Why use message queues in distributed systems? Compare Kafka and RabbitMQ.
```

#### 回答模板
```
Message queues are fundamental building blocks in distributed systems that enable 
asynchronous communication between services.

Why use message queues:

1. Decoupling:
   - Producers and consumers don't need to know about each other
   - Can evolve independently
   - Example: Order service publishes event, multiple services react

2. Asynchronous Processing:
   - Don't block the caller while processing
   - Improve response time for user-facing operations
   - Example: Send email asynchronously after user registration

3. Load Leveling:
   - Buffer requests during traffic spikes
   - Process at sustainable rate
   - Prevent system overload
   - Example: Handle Black Friday traffic surge

4. Guaranteed Delivery:
   - Messages persisted until successfully processed
   - Retry failed messages
   - No message loss even if consumer is down
   - Example: Financial transactions must be processed eventually

5. Event Sourcing:
   - Stream of events as source of truth
   - Can replay events to rebuild state
   - Audit trail of all changes
   - Example: Track all order status changes

Kafka vs RabbitMQ:

Kafka:
- Distributed streaming platform
- High throughput (millions of messages/second)
- Messages persisted on disk, retained for days/weeks
- Consumers pull messages, maintain their own offset
- Use cases: Event streaming, log aggregation, real-time analytics
- Pros: High throughput, durability, replay capability
- Cons: More complex, overkill for simple queuing

RabbitMQ:
- Traditional message broker
- Lower throughput (tens of thousands of messages/second)
- Messages deleted after consumption (by default)
- Broker pushes messages to consumers
- Use cases: Task queues, RPC, work distribution
- Pros: Flexible routing, simpler for basic queuing
- Cons: Lower throughput, messages not replayable

Comparison table:

| Feature | Kafka | RabbitMQ |
|---------|-------|----------|
| Throughput | Very High | Medium |
| Latency | Medium (ms) | Low (μs) |
| Message Retention | Yes (configurable) | No (by default) |
| Routing | Simple (topics) | Complex (exchanges) |
| Consumer Model | Pull | Push |
| Ordering | Per partition | Per queue |
| Scalability | Horizontal | Limited |

When to use Kafka:
- High-volume event streaming
- Need to replay messages
- Real-time data pipelines
- Log aggregation
- Multiple consumers reading same data

When to use RabbitMQ:
- Task queues and work distribution
- Complex routing requirements
- RPC (Remote Procedure Call)
- Lower volume messaging
- Need message acknowledgment and requeue

Example architecture with Kafka:
```
Microservices → Kafka Topics → Stream Processing → Data Store
     ↓                                              ↓
User actions                                   Analytics DB
(order placed,                                 (for dashboards)
 payment processed,
 item shipped)
```

In my experience:
- Used Kafka for event streaming and real-time analytics
- Used RabbitMQ for background job processing
- Often use both in same system for different purposes

The key is to choose based on your specific requirements:
throughput, retention, routing complexity, and consumer patterns.
```

#### 关键表达
- **message queue** - 消息队列
- **decoupling** - 解耦
- **asynchronous processing** - 异步处理
- **load leveling** - 负载均衡（流量削峰）
- **event sourcing** - 事件溯源
- **throughput** - 吞吐量
- **message retention** - 消息保留
- **consumer offset** - 消费者偏移量

---

## 常见分布式系统模式

### 7. Circuit Breaker Pattern（断路器模式）

#### 问题
```
What is the circuit breaker pattern? When should you use it?
```

#### 回答模板
```
The circuit breaker pattern prevents cascading failures in distributed systems 
by stopping calls to failing services.

The problem it solves:
- Service A calls Service B
- Service B is slow or failing
- Service A keeps calling, resources get exhausted
- Service A fails, causing Service C to fail
- Cascading failure brings down the entire system

How it works (like electrical circuit breaker):

Three states:

1. Closed (normal operation):
   - Requests flow through to the service
   - Monitor for failures
   - If failures exceed threshold, trip to Open

2. Open (circuit broken):
   - Requests fail immediately (fast fail)
   - Don't call the failing service
   - After timeout, transition to Half-Open

3. Half-Open (testing):
   - Allow limited requests through
   - If successful, close the circuit
   - If failures continue, open the circuit again

Example implementation:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = 'CLOSED'
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

Benefits:
1. Prevents cascading failures
2. Fails fast instead of waiting for timeout
3. Gives failing service time to recover
4. Provides fallback behavior

When to use:
- Calling external services (APIs, databases)
- Services with unpredictable latency
- Non-critical dependencies (can provide fallback)

When NOT to use:
- Critical path operations (must succeed)
- Local in-memory calls (overhead not worth it)
- When you need retry logic instead

Best practices:
1. Set appropriate thresholds (don't trip too easily)
2. Provide fallback behavior (cached data, default response)
3. Log circuit breaker state changes
4. Monitor and alert on circuit breaker trips
5. Use different circuit breakers for different operations

Real-world example:
In an e-commerce system:
- Payment service: Circuit breaker with fallback to queue
- Recommendation service: Circuit breaker with fallback to cached recommendations
- Inventory service: No circuit breaker (critical, must fail if unavailable)

The circuit breaker pattern is essential for building resilient distributed systems 
that can gracefully handle partial failures.
```

#### 关键表达
- **circuit breaker** - 断路器
- **cascading failure** - 级联故障
- **fail fast** - 快速失败
- **fallback** - 降级/后备方案
- **threshold** - 阈值

---

## 学习资源

- **书籍**：《Designing Data-Intensive Applications》by Martin Kleppmann
- **论文**：Raft consensus paper, Dynamo paper, CAP theorem paper
- **课程**：MIT 6.824 Distributed Systems
- **实践**：Build a simple distributed system (e.g., distributed key-value store)
