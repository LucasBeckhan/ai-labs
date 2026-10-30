# 进阶交付：主线先用ConfigMap挂代码，练完再把代码固化进镜像。
FROM python:3.12-alpine
WORKDIR /app
COPY domain.py server.py report.py ./
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_PATH=/data/operations.json
USER 10001:10001
ENTRYPOINT ["python", "/app/server.py"]
