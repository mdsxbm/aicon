# ============================================
# Stage 1: Builder - 构建阶段
# ============================================
FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv (快速Python包管理器)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 复制依赖文件
COPY pyproject.toml ./
COPY uv.lock* ./

# 使用uv安装依赖到虚拟环境
RUN uv sync --frozen --no-dev

# ============================================
# Stage 2: Runtime - 运行阶段
# ============================================
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    TZ=Asia/Shanghai

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# 设置工作目录
WORKDIR /app

# 从builder阶段复制虚拟环境
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# 复制应用代码
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./migrations ./migrations
COPY --chown=appuser:appuser ./alembic.ini ./alembic.ini

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令 (可以被docker-compose覆盖)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
