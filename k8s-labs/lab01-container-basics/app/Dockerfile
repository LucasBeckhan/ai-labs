# ---------- 构建阶段：只为了拿到 .class 文件，不会进入最终镜像 ----------
FROM eclipse-temurin:17-jdk AS build
WORKDIR /build
COPY Hello.java .
RUN javac Hello.java

# ---------- 运行阶段：只带 JRE 和产物，体积小、攻击面小 ----------
# 注意：17-jre-alpine 没有 arm64 版本（Apple Silicon 拉不到），用 jammy（Ubuntu 基础）
FROM eclipse-temurin:17-jre-jammy
# 创建非 root 用户运行（生产镜像的硬要求）；jammy 是 Ubuntu 基础，用 adduser --system
RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY --from=build /build/Hello.class .
USER app
# MaxRAMPercentage：让 JVM 按容器内存限额的比例设堆上限，而不是看宿主机内存
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "Hello"]
