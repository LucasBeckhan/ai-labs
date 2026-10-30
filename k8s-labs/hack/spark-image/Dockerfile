# 本地构建 apache/spark:v3.5.5 等价镜像（网络受限环境替代方案，已在本机验证）
# 结构对齐官方 apache/spark-docker：官方 entrypoint.sh + tini + uid 185
# 基础镜像用 eclipse-temurin:17-jdk（本地已有；官方为 17-jammy 全 JDK）
FROM eclipse-temurin:17-jdk

# 官方镜像的关键系统准备：/lib64 符号链接、/bin/sh 指向 bash（entrypoint 用到 bash 特性）
RUN ln -s /lib /lib64 && rm /bin/sh && ln -sv /bin/bash /bin/sh \
    && mkdir -p /opt/spark/work-dir && touch /opt/spark/RELEASE \
    && chmod g+w /opt/spark/work-dir \
    && chgrp root /etc/passwd && chmod ug+rw /etc/passwd

# tini 作为 PID 1（官方 entrypoint 最后 exec /usr/bin/tini -s --）
COPY tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

ENV SPARK_HOME=/opt/spark
# 官方镜像不带这行（要写全路径 /opt/spark/bin/spark-submit），这里加上方便实验命令
ENV PATH=$SPARK_HOME/bin:$PATH
WORKDIR /opt/spark/work-dir
COPY spark-3.5.5-bin-hadoop3.tgz /tmp/spark.tgz
# --no-same-owner + chown 185：cluster 模式下 Spark 会把 local: 资源拷贝到 $SPARK_HOME，
# 属主必须是运行用户，否则 AccessDeniedException（本机踩过的真实坑）
RUN tar -xzf /tmp/spark.tgz --strip-components=1 --no-same-owner -C $SPARK_HOME \
    && rm /tmp/spark.tgz \
    && chown -R 185:185 $SPARK_HOME \
    && useradd -u 185 -m spark || true

COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod 755 /opt/entrypoint.sh

ENTRYPOINT [ "/opt/entrypoint.sh" ]
USER 185
