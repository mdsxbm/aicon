# AICG内容分发平台

AI驱动的长文本到视频自动转换系统。

## 🚀 快速开始

### 1. 启动基础设施
```bash
./scripts/start.sh
```

### 2. 本地开发
```bash
cd backend
uv sync
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问服务
- API文档: http://localhost:8000/docs
- MinIO控制台: http://localhost:9001 (minioadmin/minioadmin)

## 📁 项目结构
```
aicon2/
├── README.md              # 项目说明
├── .env.example           # 环境变量模板
├── docker-compose.yml     # PostgreSQL、Redis、MinIO
├── scripts/start.sh       # 启动脚本
└── backend/               # 后端应用
```

## ⚙️ 环境配置
```bash
cp .env.example .env
# 编辑 .env 配置数据库和Redis连接
```

## 🔧 常用命令
```bash
# 启动/停止基础设施
docker-compose up -d
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [postgres|redis|minio]
```