# 云原生技术问答 (Cloud-Native Q&A)

## 核心概念

### 什么是云原生（Cloud-Native）？

云原生是一种构建和运行应用程序的方法，充分利用云计算的优势：
- **Containers（容器）**：Docker 打包应用
- **Microservices（微服务）**：拆分为小服务
- **Orchestration（编排）**：Kubernetes 管理容器
- **DevOps（开发运维一体化）**：CI/CD 自动化
- **Infrastructure as Code（基础设施即代码）**：Terraform, CloudFormation

---

## 容器技术

### 1. Docker 基础

#### 问题
```
What is Docker? How does it differ from virtual machines?
```

#### 回答模板
```
Docker is a containerization platform that packages applications with their dependencies 
into lightweight, portable containers.

Key differences from virtual machines:

Virtual Machines:
- Run a full operating system
- Hypervisor virtualizes hardware
- Heavy: typically 1-10 GB per VM
- Slow startup: minutes
- Strong isolation (separate kernel)

Containers:
- Share the host OS kernel
- Container runtime (containerd) isolates processes
- Lightweight: typically 10-100 MB per container
- Fast startup: seconds
- Process-level isolation (same kernel)

Docker architecture:
1. Dockerfile: Recipe for building an image
2. Image: Read-only template with application and dependencies
3. Container: Running instance of an image
4. Docker Engine: Client-server application that builds and runs containers

Example Dockerfile:
```dockerfile
# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]
```

Benefits of Docker:
1. Consistency: Same environment from dev to production
2. Portability: Run anywhere Docker is installed
3. Efficiency: Lower resource usage than VMs
4. Scalability: Easy to scale horizontally
5. Isolation: Applications don't interfere with each other

Common use cases:
- Microservices deployment
- CI/CD pipelines (consistent build environment)
- Local development (reproduce production environment)
- Multi-tenant applications (isolation between tenants)

Best practices:
1. Use multi-stage builds to reduce image size
2. Don't run as root (use USER instruction)
3. Use .dockerignore to exclude unnecessary files
4. Tag images with semantic versions
5. Scan images for vulnerabilities (docker scan)
6. Use official base images when possible

In my experience:
- Reduced deployment time from hours to minutes
- Eliminated "works on my machine" problems
- Enabled horizontal scaling with Kubernetes
- Improved resource utilization by 3x compared to VMs

Docker has become the de facto standard for containerization 
and is essential for modern cloud-native applications.
```

#### 关键表达
- **containerization** - 容器化
- **hypervisor** - 虚拟机监视器
- **image** - 镜像
- **container** - 容器
- **multi-stage build** - 多阶段构建
- **base image** - 基础镜像

---

### 2. Kubernetes 基础

#### 问题
```
What is Kubernetes? Explain its core components.
```

#### 回答模板
```
Kubernetes (K8s) is an open-source container orchestration platform that automates 
deployment, scaling, and management of containerized applications.

Why Kubernetes:
- Managing hundreds of containers manually is impractical
- Need automated deployment, scaling, and healing
- Need service discovery and load balancing
- Need rolling updates without downtime

Core Components:

1. Control Plane (Master Nodes):
   - API Server: Entry point for all commands (kubectl, UI, API)
   - etcd: Distributed key-value store for cluster state
   - Scheduler: Assigns pods to nodes based on resources and constraints
   - Controller Manager: Runs controllers (replication, endpoints, etc.)

2. Worker Nodes:
   - Kubelet: Agent that ensures containers are running in pods
   - Kube-proxy: Network proxy for service abstraction
   - Container Runtime: Docker, containerd, or CRI-O

3. Core Objects:
   - Pod: Smallest deployable unit (one or more containers)
   - Service: Stable network endpoint for pods
   - Deployment: Manages pod replicas and rolling updates
   - ConfigMap/Secret: Configuration and sensitive data
   - PersistentVolume: Storage abstraction

Example - Deploying a web application:
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: myapp:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Key features:
1. Self-healing: Restarts failed containers, replaces failed nodes
2. Auto-scaling: Horizontal Pod Autoscaler based on CPU/memory
3. Rolling updates: Zero-downtime deployments
4. Service discovery: DNS-based service names
5. Load balancing: Distributes traffic across pods
6. Storage orchestration: Mount various storage systems
7. Secret management: Secure handling of sensitive data

Common commands:
```bash
kubectl apply -f deployment.yaml    # Create/update resources
kubectl get pods                     # List pods
kubectl describe pod <name>         # Show pod details
kubectl logs <pod-name>             # View logs
kubectl exec -it <pod> -- /bin/sh   # Shell into pod
kubectl scale deployment web-app --replicas=5  # Scale up
kubectl rollout restart deployment/web-app     # Rolling restart
```

In production, I've used Kubernetes for:
- Deploying microservices (50+ services)
- Auto-scaling based on traffic (10x during peak)
- Blue-green deployments for zero-downtime releases
- Managing stateful applications (databases) with StatefulSets

Kubernetes has become the de facto standard for container orchestration 
and is essential for running cloud-native applications at scale.
```

#### 关键表达
- **container orchestration** - 容器编排
- **control plane** - 控制平面
- **worker node** - 工作节点
- **pod** - Pod（最小部署单元）
- **deployment** - 部署
- **service** - 服务
- **self-healing** - 自愈
- **rolling update** - 滚动更新
- **horizontal scaling** - 水平扩展

---

### 3. Kubernetes Advanced（高级概念）

#### 问题
```
Explain some advanced Kubernetes concepts like StatefulSets, DaemonSets, and Ingress.
```

#### 回答模板
```
Beyond basic Deployments and Services, Kubernetes provides several advanced 
primitives for different workloads:

1. StatefulSets (for stateful applications):
   - For applications that need stable identities and persistent storage
   - Each pod has a unique, stable identifier (pod-0, pod-1, pod-2)
   - Pods are created and terminated in order
   - Each pod gets its own PersistentVolumeClaim
   
   Use cases:
   - Databases (MySQL, PostgreSQL, MongoDB)
   - Distributed systems (Kafka, ZooKeeper, Elasticsearch)
   - Applications requiring stable network identities
   
   Example:
   ```yaml
   apiVersion: apps/v1
   kind: StatefulSet
   metadata:
     name: mysql
   spec:
     serviceName: mysql
     replicas: 3
     template:
       spec:
         containers:
         - name: mysql
           image: mysql:8.0
           volumeMounts:
           - name: data
             mountPath: /var/lib/mysql
     volumeClaimTemplates:
     - metadata:
         name: data
       spec:
         accessModes: ["ReadWriteOnce"]
         resources:
           requests:
             storage: 10Gi
   ```

2. DaemonSets (one pod per node):
   - Ensures a copy of a pod runs on all (or some) nodes
   - When nodes are added, pods are automatically created
   - When nodes are removed, pods are garbage collected
   
   Use cases:
   - Log collection (Fluentd, Filebeat)
   - Monitoring agents (Prometheus Node Exporter)
   - Network plugins (Calico, Flannel)
   - Storage daemons (Ceph, GlusterFS)
   
   Example:
   ```yaml
   apiVersion: apps/v1
   kind: DaemonSet
   metadata:
     name: log-collector
   spec:
     selector:
       matchLabels:
         app: log-collector
     template:
       metadata:
         labels:
           app: log-collector
       spec:
         containers:
         - name: fluentd
           image: fluentd:v1.14
           volumeMounts:
           - name: varlog
             mountPath: /var/log
         volumes:
         - name: varlog
           hostPath:
             path: /var/log
   ```

3. Ingress (HTTP/HTTPS routing):
   - Exposes HTTP/HTTPS routes from outside the cluster
   - Provides URL-based routing, SSL termination, name-based virtual hosting
   - Requires an Ingress Controller (Nginx, Traefik, etc.)
   
   Use cases:
   - Route traffic to different services based on URL path
   - SSL/TLS termination
   - Load balancing for HTTP services
   
   Example:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: web-ingress
     annotations:
       nginx.ingress.kubernetes.io/ssl-redirect: "true"
   spec:
     rules:
     - host: api.example.com
       http:
         paths:
         - path: /users
           pathType: Prefix
           backend:
             service:
               name: user-service
               port:
                 number: 80
         - path: /orders
           pathType: Prefix
           backend:
             service:
               name: order-service
               port:
                 number: 80
     tls:
     - hosts:
       - api.example.com
       secretName: api-tls-secret
   ```

4. Jobs and CronJobs (batch processing):
   - Jobs: Run a pod to completion (one-time tasks)
   - CronJobs: Run jobs on a schedule (periodic tasks)
   
   Use cases:
   - Database migrations
   - Batch data processing
   - Scheduled backups
   - Report generation
   
   Example:
   ```yaml
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: daily-backup
   spec:
     schedule: "0 2 * * *"  # 2 AM daily
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: backup
               image: backup-tool:latest
               command: ["/backup.sh"]
             restartPolicy: OnFailure
   ```

5. ConfigMaps and Secrets (configuration management):
   - ConfigMaps: Non-sensitive configuration data
   - Secrets: Sensitive data (passwords, tokens, keys)
   
   Use cases:
   - Application configuration
   - Database credentials
   - API keys
   - TLS certificates
   
   Example:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
   data:
     database_url: "postgres://db:5432/mydb"
     log_level: "info"
   ---
   apiVersion: v1
   kind: Secret
   metadata:
     name: db-credentials
   type: Opaque
   data:
     username: YWRtaW4=  # base64 encoded
     password: cGFzc3dvcmQ=
   ```

In production, I've used:
- StatefulSets for running Kafka and Elasticsearch clusters
- DaemonSets for log collection with Fluentd
- Ingress for routing API traffic with SSL termination
- CronJobs for daily database backups and report generation
- ConfigMaps and Secrets for managing application configuration

These advanced primitives enable Kubernetes to handle a wide variety 
of workloads beyond simple stateless web services.
```

#### 关键表达
- **StatefulSet** - 有状态集
- **DaemonSet** - 守护进程集
- **Ingress** - 入口
- **Job / CronJob** - 作业 / 定时作业
- **ConfigMap / Secret** - 配置映射 / 密钥
- **PersistentVolume** - 持久卷
- **SSL termination** - SSL 终止

---

### 4. Service Mesh（服务网格）

#### 问题
```
What is a service mesh? When would you use Istio or Linkerd?
```

#### 回答模板
```
A service mesh is a dedicated infrastructure layer for managing service-to-service 
communication in microservices architectures.

The problem it solves:
In microservices, you have dozens or hundreds of services communicating with each other. 
Each service needs to handle:
- Service discovery
- Load balancing
- Encryption (mTLS)
- Authentication and authorization
- Observability (metrics, logs, traces)
- Resilience (retries, timeouts, circuit breaking)

Without a service mesh, each service must implement these concerns, leading to:
- Duplicated logic across services
- Inconsistent behavior
- Hard to update policies globally
- Difficult to observe end-to-end

How it works:
1. Sidecar proxy deployed alongside each service (Envoy, Linkerd-proxy)
2. All traffic flows through the proxy
3. Control plane manages configuration and policies
4. Data plane (proxies) handles actual traffic

Architecture:
```
Control Plane (Istiod / Linkerd Controller)
    ↓ (configuration)
┌─────────────────────────────────────┐
│ Service A    │ Service B            │
│ ┌──────────┐ │ ┌──────────┐         │
│ │App       │ │ │App       │         │
│ └──────────┘ │ └──────────┘         │
│ ┌──────────┐ │ ┌──────────┐         │
│ │Sidecar   │←→│Sidecar   │         │
│ │Proxy     │ │Proxy     │         │
│ └──────────┘ │ └──────────┘         │
└─────────────────────────────────────┘
         Data Plane (proxies)
```

Key features:

1. Traffic Management:
   - Fine-grained routing (canary, A/B testing)
   - Traffic splitting and mirroring
   - Fault injection for testing
   - Retries and timeouts

2. Security:
   - Mutual TLS (mTLS) between services
   - Automatic certificate rotation
   - Fine-grained access policies
   - Authentication (JWT, OAuth)

3. Observability:
   - Distributed tracing (Jaeger, Zipkin)
   - Metrics (request rate, latency, errors)
   - Access logs
   - Service dependency graph

4. Resilience:
   - Circuit breaking
   - Rate limiting
   - Health checking
   - Automatic retries

Istio vs Linkerd:

Istio:
- More features, more complex
- Larger community, backed by Google/IBM
- Uses Envoy proxy
- Better for large, complex deployments
- Steeper learning curve

Linkerd:
- Simpler, lighter weight
- Easier to install and operate
- Uses custom proxy (micro-proxy)
- Better for smaller deployments
- Lower resource overhead

When to use a service mesh:

Use when:
- 20+ microservices
- Need fine-grained traffic control (canary, A/B)
- Require mTLS between all services
- Need distributed tracing across services
- Multiple teams managing different services

Don't use when:
- Small number of services (< 10)
- Simple request routing is sufficient
- Team doesn't have Kubernetes expertise
- Performance overhead is critical (adds 1-5ms latency)

Example - Canary deployment with Istio:
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 90  # 90% traffic to v1
    - destination:
        host: reviews
        subset: v2
      weight: 10  # 10% traffic to v2 (canary)
```

In my experience:
- Implemented Istio for a platform with 50+ microservices
- Enabled mTLS for all service-to-service communication
- Used traffic splitting for gradual rollouts
- Integrated with Jaeger for distributed tracing
- Reduced time to diagnose cross-service issues from hours to minutes

The service mesh pattern is becoming standard for large-scale microservices 
deployments, but it adds complexity that may not be justified for smaller systems.
```

#### 关键表达
- **service mesh** - 服务网格
- **sidecar proxy** - 边车代理
- **control plane / data plane** - 控制平面 / 数据平面
- **mutual TLS (mTLS)** - 双向 TLS
- **distributed tracing** - 分布式追踪
- **canary deployment** - 金丝雀部署
- **traffic splitting** - 流量分割

---

### 5. Infrastructure as Code（基础设施即代码）

#### 问题
```
What is Infrastructure as Code? Compare Terraform and CloudFormation.
```

#### 回答模板
```
Infrastructure as Code (IaC) is the practice of managing and provisioning infrastructure 
through code and automation, rather than manual processes.

Benefits of IaC:
1. Version control: Track changes to infrastructure like application code
2. Reproducibility: Recreate environments exactly (dev, staging, production)
3. Automation: Eliminate manual, error-prone setup
4. Collaboration: Review infrastructure changes like code reviews
5. Documentation: Code serves as documentation of infrastructure
6. Testing: Test infrastructure changes before applying

Terraform vs CloudFormation:

Terraform (HashiCorp):
- Multi-cloud: AWS, Azure, GCP, on-premises
- Uses HCL (HashiCorp Configuration Language)
- State file tracks current infrastructure state
- Large provider ecosystem
- Open source with commercial offerings

Example Terraform code:
```hcl
# Create AWS EC2 instance
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  
  tags = {
    Name = "web-server"
  }
}

# Create S3 bucket
resource "aws_s3_bucket" "data" {
  bucket = "my-app-data"
  acl    = "private"
}
```

CloudFormation (AWS):
- AWS-only (but comprehensive AWS coverage)
- Uses JSON or YAML
- Stack-based (group of resources)
- Integrated with AWS services
- No state file (AWS manages state)

Example CloudFormation code:
```yaml
Resources:
  WebServer:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c55b159cbfafe1f0
      InstanceType: t2.micro
      Tags:
        - Key: Name
          Value: web-server
  
  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-app-data
      AccessControl: Private
```

Comparison:

| Feature | Terraform | CloudFormation |
|---------|-----------|----------------|
| Multi-cloud | Yes | AWS only |
| Language | HCL | JSON/YAML |
| State management | Local or remote file | AWS managed |
| Learning curve | Moderate | Steeper |
| Community | Large | AWS-focused |
| Drift detection | terraform plan | Drift Detection feature |

When to use Terraform:
- Multi-cloud or hybrid cloud environments
- Need to manage resources across multiple providers
- Team already familiar with Terraform
- Need strong community and third-party modules

When to use CloudFormation:
- AWS-only environments
- Deep integration with AWS services needed
- Team already AWS-certified and experienced
- Prefer AWS-managed state management

Best practices:
1. Use version control (Git) for all IaC code
2. Use modules for reusable components
3. Separate environments (dev/staging/prod) with different state
4. Use remote state storage (S3, Terraform Cloud) for collaboration
5. Implement code review process for infrastructure changes
6. Use terraform plan / cloudformation diff to preview changes
7. Automate with CI/CD pipelines
8. Use variables and parameters for flexibility
9. Tag all resources for cost tracking and management
10. Implement least privilege for IaC execution roles

Example workflow:
```
Developer writes Terraform code
    ↓
Commit to Git repository
    ↓
CI pipeline runs terraform plan
    ↓
Code review (review plan output)
    ↓
Merge to main branch
    ↓
CD pipeline runs terraform apply
    ↓
Infrastructure updated
```

In my experience:
- Used Terraform to manage multi-cloud infrastructure (AWS + on-premises)
- Created reusable modules for common patterns (VPC, ECS cluster, RDS)
- Implemented GitOps workflow with automated plan and apply
- Reduced infrastructure provisioning time from days to minutes
- Enabled developers to self-service infrastructure through PRs

IaC is essential for modern cloud-native development and enables teams 
to manage infrastructure with the same rigor as application code.
```

#### 关键表达
- **Infrastructure as Code (IaC)** - 基础设施即代码
- **provisioning** - 配置/供应
- **state file** - 状态文件
- **drift detection** - 漂移检测
- **module** - 模块
- **GitOps** - Git 运维

---

## CI/CD 最佳实践

### 6. CI/CD Pipeline（持续集成/持续部署）

#### 问题
```
Describe a CI/CD pipeline you've implemented. What are the key stages?
```

#### 回答模板
```
CI/CD (Continuous Integration / Continuous Deployment) automates the process of 
integrating code changes and deploying them to production.

I implemented a CI/CD pipeline for a microservices platform with the following stages:

Stage 1: Code Commit
- Developer pushes code to Git repository (GitHub/GitLab)
- Webhook triggers the CI/CD pipeline
- Branch protection rules require PR review and passing CI

Stage 2: Build and Test (CI)
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build
        run: make build
      
      - name: Unit Tests
        run: make test-unit
      
      - name: Integration Tests
        run: make test-integration
      
      - name: Code Quality
        run: make lint
      
      - name: Security Scan
        run: make security-scan
```

Stage 3: Build Docker Image
```yaml
- name: Build Docker Image
  run: |
    docker build -t myapp:${{ github.sha }} .
    docker tag myapp:${{ github.sha }} myapp:latest

- name: Push to Registry
  run: |
    docker push myapp:${{ github.sha }}
    docker push myapp:latest
```

Stage 4: Deploy to Staging (CD - Automatic)
```yaml
- name: Deploy to Staging
  if: github.ref == 'refs/heads/main'
  run: |
    kubectl set image deployment/myapp \
      myapp=myapp:${{ github.sha }} \
      --namespace staging
    
    kubectl rollout status deployment/myapp \
      --namespace staging \
      --timeout=5m
```

Stage 5: Smoke Tests (Staging)
```yaml
- name: Smoke Tests
  run: |
    ./scripts/smoke-test.sh https://staging.myapp.com
```

Stage 6: Deploy to Production (CD - Manual Approval)
```yaml
- name: Deploy to Production
  if: github.ref == 'refs/heads/main'
  environment:
    name: production
    url: https://myapp.com
  run: |
    kubectl set image deployment/myapp \
      myapp=myapp:${{ github.sha }} \
      --namespace production
    
    kubectl rollout status deployment/myapp \
      --namespace production \
      --timeout=10m
```

Stage 7: Post-Deployment
```yaml
- name: Health Check
  run: |
    ./scripts/health-check.sh https://myapp.com

- name: Notify Team
  run: |
    ./scripts/notify-slack.sh "Deployed ${{ github.sha }} to production"
```

Key features of the pipeline:

1. Automated Testing:
   - Unit tests (>80% coverage required)
   - Integration tests (API contract testing)
   - Security scanning (SAST, dependency check)
   - Performance tests (load testing on staging)

2. Progressive Deployment:
   - Deploy to staging automatically
   - Manual approval for production
   - Canary deployment (10% → 50% → 100%)
   - Automatic rollback on health check failure

3. Observability:
   - Deployment notifications to Slack
   - Metrics collection (deployment frequency, lead time)
   - Distributed tracing enabled
   - Structured logging with correlation IDs

4. Security:
   - Secrets managed via Kubernetes Secrets (encrypted)
   - Image scanning with Trivy
   - RBAC for deployment permissions
   - Audit log of all deployments

Metrics we tracked:
- Deployment frequency: 15-20 deployments per day
- Lead time for changes: < 1 hour from commit to production
- Change failure rate: < 5%
- Mean time to recovery: < 15 minutes

Benefits achieved:
- Reduced deployment time from 2 hours to 15 minutes
- Eliminated manual deployment errors
- Enabled developers to deploy independently
- Improved release confidence with automated testing
- Faster time to market for new features

The key is to start simple and iterate:
1. Basic CI (build + test)
2. Add automated deployment to staging
3. Add manual approval for production
4. Add canary deployments
5. Add advanced features (feature flags, A/B testing)

This progressive approach allows teams to adopt CI/CD practices 
without being overwhelmed by complexity.
```

#### 关键表达
- **CI/CD pipeline** - 持续集成/持续部署管道
- **build artifact** - 构建产物
- **deployment strategy** - 部署策略
- **canary deployment** - 金丝雀部署
- **blue-green deployment** - 蓝绿部署
- **rollback** - 回滚
- **feature flag** - 特性开关

---

## 学习资源

- **书籍**：《Kubernetes in Action》, 《Terraform: Up & Running》
- **认证**：CKA (Certified Kubernetes Administrator), AWS Solutions Architect
- **实验**：Minikube, Kind, Docker Desktop with Kubernetes
- **课程**：Kubernetes the Hard Way (Kelsey Hightower)
- **社区**：CNCF (Cloud Native Computing Foundation)
