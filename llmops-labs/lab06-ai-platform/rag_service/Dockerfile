# RAG 服务镜像：glibc 基础（chromadb 的 onnxruntime 依赖），pip 走阿里云源
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
COPY main.py .
COPY knowledge ./knowledge
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
