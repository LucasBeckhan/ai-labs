# 系统设计问答 (System Design Q&A)

## 核心概念

### 系统设计面试流程

1. **Clarify Requirements** - 澄清需求
2. **Estimate Scale** - 估算规模
3. **Define APIs** - 定义 API
4. **Design Database** - 设计数据库
5. **High-Level Design** - 高层设计
6. **Detailed Design** - 详细设计
7. **Identify Bottlenecks** - 识别瓶颈
8. **Scale the Design** - 扩展设计

---

## 常用表达

### 澄清需求
```
Before diving into the design, let me clarify a few things:
- What's the expected number of users?
- What are the core features we need to support?
- Are there any latency requirements?
- What's the read/write ratio?
- Do we need to support real-time updates?
```

### 估算规模
```
Let me do some back-of-the-envelope calculations:
- Assuming we have X million daily active users
- Each user makes approximately Y requests per day
- That gives us Z requests per second on average
- For peak traffic, we should design for 2-3x the average
```

### 高层设计
```
At a high level, the system consists of the following components:
- A load balancer to distribute traffic
- Multiple application servers for handling requests
- A caching layer to reduce database load
- A database for persistent storage
- A message queue for asynchronous processing

Let me walk you through the data flow:
```

### 数据库设计
```
For the database, I would choose [database type] because:
- It provides [advantage 1]
- It supports [advantage 2]
- It's well-suited for [use case]

The schema would look like this:
- Table X with fields A, B, C
- Indexes on fields A and B for fast lookups
- Partitioning strategy based on field C
```

### 扩展设计
```
To handle scale, I would:
- Add horizontal scaling by adding more servers
- Implement sharding to partition the database
- Add caching at multiple levels
- Use CDN for static content
- Implement rate limiting to prevent abuse
```

---

## 经典系统设计问题

### 1. Design a URL Shortener (设计 URL 短链接服务)

#### 问题描述
```
Design a URL shortening service like bit.ly or tinyurl.com.
Requirements:
- Given a long URL, generate a short URL
- When the short URL is accessed, redirect to the original URL
- Support 100 million URLs per month
- Short URLs should be 7 characters or less
```

#### 澄清问题
```
Let me clarify a few things:
- What's the read-to-write ratio? (Assume 10:1)
- Do we need analytics? (Yes, track click counts)
- Should short URLs be customizable? (Optional feature)
- What's the latency requirement? (< 100ms for redirects)
- Do short URLs expire? (No, unless explicitly deleted)
```

#### 规模估算
```
Let me estimate the scale:
- 100 million new URLs per month
- That's about 40 URLs per second (write)
- With 10:1 read ratio, that's 400 redirects per second (read)
- Over 5 years: 100M × 12 × 5 = 6 billion URLs
- Each URL record: ~500 bytes (long URL, short code, metadata)
- Total storage: 6B × 500 bytes = 3 TB

For short URL length:
- 7 characters using base62 (a-z, A-Z, 0-9)
- 62^7 = 3.5 trillion possible combinations
- More than enough for 6 billion URLs
```

#### API 设计
```
POST /api/v1/shorten
Request: { "long_url": "https://example.com/very/long/url" }
Response: { "short_url": "https://short.ly/abc123" }

GET /{short_code}
Response: 301 redirect to long_url

GET /api/v1/analytics/{short_code}
Response: { "clicks": 1234, "unique_visitors": 890 }
```

#### 高层设计
```
Components:
1. Load Balancer - distributes traffic
2. Web Servers - handle API requests
3. Short URL Generator - generates unique short codes
4. Database - stores URL mappings
5. Cache - stores frequently accessed URLs
6. Analytics Service - tracks click statistics

Data Flow:
1. User submits long URL to load balancer
2. Load balancer forwards to web server
3. Web server calls short URL generator
4. Generator creates unique short code
5. Web server stores mapping in database
6. Web server caches the mapping
7. Web server returns short URL to user

For redirects:
1. User accesses short URL
2. Load balancer forwards to web server
3. Web server checks cache first
4. If cache miss, query database
5. Return 301 redirect to long URL
6. Asynchronously log the click for analytics
```

#### 详细设计

**短码生成策略**
```
Option 1: Base62 encoding of database ID
- Simple but predictable (security concern)
- Example: ID 12345 → "dnh"

Option 2: MD5 hash of long URL, take first 7 chars
- Handles duplicates (same long URL → same short code)
- Risk of collisions (need to handle)

Option 3: Random generation with collision detection
- Most flexible
- Check database before inserting
- Retry if collision detected

I would choose Option 3 for unpredictability and flexibility.
```

**数据库设计**
```
URL_Mapping table:
- short_code (string, primary key, indexed)
- long_url (string, indexed)
- created_at (timestamp)
- expires_at (timestamp, nullable)
- user_id (foreign key, nullable)

Analytics table:
- short_code (foreign key)
- timestamp
- ip_address
- user_agent
- referrer

Indexing strategy:
- Primary index on short_code for fast lookups
- Secondary index on long_url to detect duplicates
- Partition Analytics table by month for efficient queries
```

**缓存策略**
```
- Use Redis for caching
- Cache frequently accessed short URLs
- TTL: 24 hours or until URL is deleted
- Cache size: 20% of total URLs (80/20 rule)
- Eviction policy: LRU (Least Recently Used)

Cache flow:
1. Check cache for short_code
2. If hit, return long_url immediately
3. If miss, query database
4. Store result in cache
5. Return long_url
```

**扩展设计**
```
To handle scale:
1. Database sharding
   - Shard by short_code hash
   - 16 shards initially, can scale to 256
   - Each shard handles ~25M URLs

2. Horizontal scaling
   - Add more web servers behind load balancer
   - Stateless servers, easy to scale

3. Multi-level caching
   - L1: Application server local cache (small, fast)
   - L2: Redis cluster (larger, shared)

4. CDN for redirects
   - Cache redirects at CDN edge
   - Reduces load on origin servers

5. Asynchronous analytics
   - Use message queue (Kafka) for click events
   - Process analytics asynchronously
```

---

### 2. Design a Chat Application (设计聊天应用)

#### 问题描述
```
Design a real-time chat application like WhatsApp or WeChat.
Requirements:
- One-on-one and group chats
- Message delivery guarantee
- Online/offline status
- Push notifications for offline users
- Support 100 million daily active users
```

#### 关键设计决策

**消息存储**
```
Option 1: Store in sender's and receiver's message boxes
- Pros: Easy to query user's messages
- Cons: Duplication, consistency issues

Option 2: Store once, reference from multiple places
- Pros: No duplication, single source of truth
- Cons: More complex queries

I would choose Option 2 for efficiency and consistency.
```

**消息传递**
```
Online users:
- Use WebSocket for real-time delivery
- Maintain persistent connection
- Send message immediately

Offline users:
- Store message in database
- Send push notification
- Deliver when user comes online

Message delivery guarantee:
- Use message acknowledgment (ACK)
- Retry if no ACK received
- Idempotency keys to prevent duplicates
```

**数据库设计**
```
Users table:
- user_id (primary key)
- username
- status (online/offline)
- last_seen

Messages table:
- message_id (primary key)
- sender_id (foreign key)
- chat_id (foreign key)
- content
- timestamp
- status (sent/delivered/read)

Chats table:
- chat_id (primary key)
- type (one-on-one/group)
- participants (array of user_ids)
- created_at

Chat_Participants table:
- chat_id (foreign key)
- user_id (foreign key)
- joined_at
- role (admin/member)
```

**扩展设计**
```
1. Connection layer
   - Multiple WebSocket servers
   - Each server handles ~100K connections
   - Use consistent hashing to route users

2. Message queue
   - Use Kafka for message buffering
   - Handles traffic spikes
   - Ensures message durability

3. Database sharding
   - Shard Messages table by chat_id
   - Shard Users table by user_id
   - Use different databases for different data types

4. Presence service
   - Separate service for online status
   - Use Redis for fast lookups
   - Heartbeat mechanism to detect offline users
```

---

### 3. Design a News Feed System (设计新闻推送系统)

#### 问题描述
```
Design a news feed system like Twitter or Facebook.
Requirements:
- Users can post updates (text, images, videos)
- Users follow other users
- News feed shows posts from followed users
- Support 500 million users, 1 billion posts
```

#### 关键设计决策

**推送模型 vs 拉取模型**
```
Push model (Fan-out on write):
- When user posts, immediately push to all followers' feeds
- Pros: Fast read, feed is pre-computed
- Cons: Slow write, high storage for celebrities

Pull model (Fan-out on read):
- When user opens feed, pull posts from followed users
- Pros: Fast write, less storage
- Cons: Slow read, complex queries

Hybrid approach (recommended):
- Push for normal users (< 10K followers)
- Pull for celebrities (> 10K followers)
- Balance between read and write performance
```

**数据库设计**
```
Posts table:
- post_id (primary key)
- user_id (foreign key)
- content
- media_urls
- created_at

Follows table:
- follower_id (foreign key)
- followee_id (foreign key)
- created_at
- Primary key: (follower_id, followee_id)

Feeds table (for push model):
- user_id (foreign key)
- post_id (foreign key)
- created_at
- Partitioned by user_id
```

**扩展设计**
```
1. Feed generation
   - Use message queue for asynchronous processing
   - Separate service for feed generation
   - Batch processing for efficiency

2. Caching strategy
   - Cache user's feed in Redis
   - Invalidate on new posts
   - TTL: 1 hour

3. Media handling
   - Store media in object storage (S3)
   - Use CDN for delivery
   - Generate thumbnails asynchronously

4. Ranking algorithm
   - Score based on recency, engagement, relevance
   - Machine learning model for personalization
   - A/B testing for optimization
```

---

## 系统设计评估标准

### 功能完整性
- [ ] 满足所有功能需求
- [ ] 考虑边界情况和错误处理
- [ ] 支持未来功能扩展

### 可扩展性
- [ ] 水平扩展能力
- [ ] 数据库分片策略
- [ ] 缓存策略合理
- [ ] 异步处理机制

### 性能和延迟
- [ ] 满足延迟要求
- [ ] 识别和优化瓶颈
- [ ] 合理的缓存策略
- [ ] 负载均衡设计

### 可靠性和可用性
- [ ] 单点故障处理
- [ ] 数据备份和恢复
- [ ] 监控和告警
- [ ] 优雅降级

### 安全性
- [ ] 认证和授权
- [ ] 数据加密
- [ ] API 限流
- [ ] 防止常见攻击（SQL 注入、XSS 等）

---

## 练习建议

1. **每周练习 2-3 个系统设计问题**
2. **使用白板或绘图工具画图**
3. **计时练习（45 分钟内完成）**
4. **录音回答，回听改进**
5. **和朋友做模拟面试**

## 推荐资源

- **书籍**：《Designing Data-Intensive Applications》
- **课程**：Grokking the System Design Interview
- **网站**：system-design-primer on GitHub
- **视频**：YouTube 上的系统设计面试视频
