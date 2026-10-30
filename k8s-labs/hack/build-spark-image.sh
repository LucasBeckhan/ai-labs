#!/bin/bash
# ============================================================================
# build-spark-image.sh —— 本地构建 apache/spark:v3.5.5 等价镜像
#
# 【这个脚本是干什么的】
#   Lab 10 需要 apache/spark:v3.5.5 镜像（约 700MB）。网络受限时 Docker Hub
#   拉不到它，本脚本提供替代路径：**本地构建一个等价镜像**，三样材料：
#     ① Spark 3.5.5 二进制包 —— 从华为云镜像站下载（国内直连快）
#     ② entrypoint.sh        —— 就在二进制包内部的 kubernetes/dockerfiles/ 目录里
#                               （官方镜像的启动脚本，处理 driver/executor 启动方式）
#     ③ tini                 —— 官方镜像用作 1 号进程的小工具，从 GitHub Releases
#                               经 gh-proxy 代理下载（arm64 静态版）
#   然后用 Dockerfile（同目录）把三者组装成 apache/spark:v3.5.5。
#
# 【怎么运行】
#   cd ~/Documents/ai-labs/k8s-labs
#   ./hack/build-spark-image.sh          # 构建（首次约 10 分钟，含下载）
#   ./hack/build-spark-image.sh          # 再跑一次会自动跳过已完成的步骤
#
# 【为什么不用官方镜像】官方镜像在 Docker Hub，网络受限时拉不到；
#   本脚本的全部下载源（华为云/gh-proxy）都在国内可达，已在本机验证。
# ============================================================================
set -euo pipefail
# set -euo pipefail 三连的含义（比单独 set -u 更严格）：
#   -e  任何命令失败立即退出（不带病运行）
#   -u  使用未定义变量立即报错
#   -o pipefail  管道中任何一个命令失败都算整体失败（默认只看最后一个）

# cd 到脚本所在目录的 spark-image 子目录（Dockerfile 就在那里），
# "$(dirname "$0")" 的写法保证：无论你从哪个目录执行本脚本，路径都不会错
cd "$(dirname "$0")/spark-image"

# ----------------------------------------------------------------------------
# 第 1 部分：版本与下载地址定义
# ----------------------------------------------------------------------------
VER=3.5.5                                   # Spark 版本号（改这里可以构建其他版本）
TGZ="spark-${VER}-bin-hadoop3.tgz"          # 二进制包文件名（约 400MB，下载一次永久保留）
MIRROR="https://mirrors.huaweicloud.com/apache/spark/spark-${VER}/${TGZ}"   # 华为云镜像站直链
# gh-proxy 是 GitHub 的下载代理：tini 原地址在 github.com，国内直连不稳定
TINI_URL="https://gh-proxy.com/https://github.com/krallin/tini/releases/download/v0.19.0/tini-static-arm64"

# ----------------------------------------------------------------------------
# 第 2 部分：镜像已存在则跳过（幂等——重复运行不会重复构建）
# ----------------------------------------------------------------------------
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -qx "apache/spark:v${VER}"; then
  echo "SKIP apache/spark:v${VER} 已存在"
else
  # 材料①：Spark 二进制包。-A "Mozilla/5.0" 是浏览器 UA（部分镜像站拒绝 curl 默认 UA）
  if [ ! -f "$TGZ" ]; then
    echo ">>> 下载 Spark 二进制包（约 400MB，来自华为云镜像站）"
    curl -L -A "Mozilla/5.0" "$MIRROR" -o "$TGZ"
  fi

  # 材料②：tini 静态二进制（官方 entrypoint 最后会 exec /usr/bin/tini，缺了起不来）
  if [ ! -s tini ]; then
    echo ">>> 下载 tini（经 GitHub 代理）"
    curl -sL --connect-timeout 15 "$TINI_URL" -o tini
  fi

  # 材料③：构建。Dockerfile 里的三步分解见同目录 Dockerfile 的逐行注释
  echo ">>> docker build（把 400MB 包解压进镜像，需要几分钟）"
  docker build -t apache/spark:v${VER} .
fi

# ----------------------------------------------------------------------------
# 第 3 部分：注入 kind 集群（集群存在时才执行）
# 同 prepare-images.sh 的原理：kind 节点看不到 Docker Desktop 的本地镜像，必须 load
# ----------------------------------------------------------------------------
if kind get clusters 2>/dev/null | grep -q labs; then
  echo ">>> 注入 kind 集群（大镜像，需要一两分钟）"
  kind load docker-image apache/spark:v${VER} --name labs
fi

echo "=== 完成：apache/spark:v${VER} 已就绪，可以去 Lab 10 提交 SparkPi 了 ==="
