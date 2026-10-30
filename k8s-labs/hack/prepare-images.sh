#!/bin/bash
# ============================================================================
# prepare-images.sh —— 实验镜像一键准备（线性版：每一步一条命令，每行都有注释）
#
# 【这个脚本是干什么的】
#   kind 集群拉取镜像时不走 Docker Desktop 的代理配置，直接访问镜像仓库。
#   国内网络下（或本机代理没开）会卡在 ImagePullBackOff。
#   所以开始实验前，先用本脚本把所有实验需要的镜像准备好，分三步：
#     第 1 步：逐个 docker pull（直连失败自动换国内镜像站重试）
#     第 2 步：docker tag 把"镜像站名字"改回"标准名字"（让 YAML 里的 image: 可用）
#     第 3 步：kind load docker-image 把镜像注入 kind 节点（之后实验不再访问外网）
#
# 【怎么运行】
#   cd ~/Documents/ai-labs/k8s-labs
#   chmod +x hack/prepare-images.sh
#   ./hack/prepare-images.sh
#
# 【安全性】已拉过的镜像自动跳过（SKIP），重复运行是安全的。
# ============================================================================

# set -u 的作用：使用了未定义的变量时立即报错退出（避免脚本带病运行到一半出错更难查）
set -u

# ----------------------------------------------------------------------------
# 第 0 部分：定义两个国内镜像站的地址（后面反复使用，统一放这里好维护）
# ----------------------------------------------------------------------------
DAOCLOUD="docker.m.daocloud.io"   # 镜像站 1：DaoCloud（对 docker.io 和 registry.k8s.io 都有代理）
MS="docker.1ms.run"               # 镜像站 2：备用站点（主站限流/超时时自动换它重试）

# ----------------------------------------------------------------------------
# 第 1 部分：实验需要的全部镜像清单（写的是"标准名字"，也就是 YAML 里 image: 的名字）
# 想加新镜像？往数组里加一行 "镜像名:标签" 即可。
# ----------------------------------------------------------------------------
IMAGES=(
  "kindest/node:v1.31.4"                                       # kind 集群节点本身（创建集群时用）
  "eclipse-temurin:17-jdk"                                     # Lab01 Java 编译阶段的基础镜像
  "eclipse-temurin:17-jre-jammy"                               # Lab01 Java 运行阶段基础镜像（jammy=Ubuntu 22.04）
  "python:3.12-alpine"                                         # Lab02/03/05/06/09 的演示应用
  "busybox:1.36"                                               # 各实验通用的迷你工具镜像（sleep/nslookup）
  "nginx:1.27"                                                 # Lab03/07 的 web 服务
  "mysql:8.0"                                                  # Lab04 数据库
  "curlimages/curl:8.10.1"                                     # Lab07/09 在集群内发 HTTP 请求用
  "apache/spark:v3.5.5"                                        # Lab10 Spark（网络受限时改用 build-spark-image.sh 本地构建）
  "prom/prometheus:v3.2.1"                                     # Lab10 监控：Prometheus
  "grafana/grafana:11.5.1"                                     # Lab10 监控：Grafana
  "registry.k8s.io/metrics-server/metrics-server:v0.7.2"       # Lab09 HPA 的指标来源（注意：k8s 官方仓库）
  "registry.k8s.io/ingress-nginx/controller:v1.11.3"           # Lab07 Ingress 控制器（k8s 官方仓库）
  "registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.4.4"  # Lab07 Ingress 的证书生成任务
)

# ----------------------------------------------------------------------------
# 第 2 部分：两个工具函数
# ----------------------------------------------------------------------------

# ok_pull 函数：执行一次 docker pull，并判断到底成功没有。
# 成功标志：输出里出现 "Status: Downloaded" 或 "Status: Image is up to date"。
# ⚠ 两个实测踩过的坑（写在这里防止后人再踩）：
#   坑 1：macOS 自带的 bash 没有 GNU timeout 命令——写成 "timeout 900 docker pull"
#         会因 timeout 不存在而瞬间失败，错误被吞掉后看起来像"所有镜像站都挂了"
#   坑 2：判断成功要 grep 完整的成功短语。只取输出的最后一行会拿到镜像名而漏判成功
ok_pull () {
  docker pull "$1" 2>&1 | grep -qE "Status: Downloaded|Status: Image is up to date"
}

# have 函数：判断某个镜像本地是否已存在（存在就跳过，避免重复下载浪费几分钟）
have () { docker images --format '{{.Repository}}:{{.Tag}}' | grep -qx "$1"; }

# ----------------------------------------------------------------------------
# 第 3 部分：主循环 —— 逐个镜像完成"拉取 + 改名"
# ----------------------------------------------------------------------------
for target in "${IMAGES[@]}"; do

  # 3.1 本地已有这个镜像（标准名）→ 跳过，不重复下载
  if have "$target"; then
    echo "SKIP $target (已有)"
    continue
  fi

  # 3.2 生成"尝试顺序"列表：
  #     第一个候选永远是标准名本身 —— 如果你开了 VPN/网络畅通，直连就成功；
  #     直连失败时，再逐个尝试后面的国内镜像站等价路径。
  CANDIDATES=("$target")

  # registry.k8s.io 的镜像站代理路径规则和 docker.io 不同（保留仓库前缀），单独处理
  case "$target" in
    registry.k8s.io/*)
      CANDIDATES+=("m.daocloud.io/$target")          # DaoCloud 的 k8s 官方仓库代理路径
      CANDIDATES+=("$MS/$target")                    # 1ms 的 k8s 官方仓库代理路径
      ;;
    *)
      # docker.io 官方镜像（python/nginx/mysql 等）在镜像站常挂在 library/ 下，
      # 组织镜像（curlimages 等）不挂 —— 所以两种路径都放进候选列表
      CANDIDATES+=("$DAOCLOUD/$target")              # DaoCloud 原路径
      CANDIDATES+=("$DAOCLOUD/library/$target")      # DaoCloud library/ 路径（官方镜像）
      CANDIDATES+=("$MS/$target")                    # 1ms 原路径
      CANDIDATES+=("$MS/library/$target")            # 1ms library/ 路径（官方镜像）
      ;;
  esac

  # 3.3 按候选顺序逐个尝试拉取，任何一个成功就打标签并结束本镜像的尝试
  DONE=0
  for src in "${CANDIDATES[@]}"; do
    echo ">>> [$target] 尝试 $src"
    if ok_pull "$src"; then
      # 关键一步：把"镜像站名字"打回"标准名字"。
      # 这样 YAML 清单里依然写 nginx:1.27 就能跑，不必把所有清单改成镜像站地址
      # （标准名 = 可移植性）。src 就是标准名时（直连成功）不需要 tag。
      if [ "$src" != "$target" ]; then
        docker tag "$src" "$target"
      fi
      echo "OK  $target"
      DONE=1
      break
    fi
  done

  # 3.4 所有候选都失败：明确报告失败（不静默吞掉），提示检查网络
  if [ $DONE -eq 0 ]; then
    echo "FAIL $target （所有来源都失败，检查网络或手动处理）"
  fi

done   # 主循环结束

# ----------------------------------------------------------------------------
# 第 4 部分：把准备好的镜像注入 kind 集群
# 为什么需要这一步：kind 节点用自己的 containerd（不是 Docker Desktop 的镜像库），
# 看不到你 docker pull 下来的镜像，必须用 kind load "灌"进节点。
# ----------------------------------------------------------------------------
if kind get clusters 2>/dev/null | grep -q labs; then
  echo "=== 第 4 步：加载镜像进 kind 集群（每个镜像几秒到几十秒） ==="
  for target in "${IMAGES[@]}"; do
    # 只加载本地确实存在的镜像（第 3 步拉取失败的跳过，不中断整个流程）
    if have "$target"; then
      # kind load 的输出很长（每个镜像两行提示），重定向丢弃，只打印我们的结果行
      if kind load docker-image "$target" --name labs > /dev/null 2>&1; then
        echo "loaded: $target"
      else
        echo "load 失败: $target（可重新运行本脚本重试）"
      fi
    fi
  done
  echo "=== 完成：所有实验镜像已就绪，可以开始做实验了 ==="
else
  # 集群还没创建时，不自动创建（初学者应按 README 的节奏手动执行），给出下一步指引
  echo "=== 未发现 labs 集群。请先创建集群，然后重新运行本脚本： ==="
  echo "    kind create cluster --config kind-config.yaml"
fi

# ----------------------------------------------------------------------------
# 第 5 部分：最后打印本地镜像清单（过滤掉镜像站的中间名字，只看最终结果）
# ----------------------------------------------------------------------------
echo "=== 当前本地镜像清单 ==="
docker images --format '{{.Repository}}:{{.Tag}}' | grep -vE "daocloud|1ms.run" | sort
