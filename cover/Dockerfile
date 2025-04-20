# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装（使用清华镜像源）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制代码
COPY app.py .

# 容器监听端口
EXPOSE 5678

# 启动服务
CMD ["python", "app.py"]