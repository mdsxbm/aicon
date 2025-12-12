# 📦 安装部署指南

本文档提供AICG平台的详细安装和部署说明。

---

## 📋 前置要求

### 系统要求

| 工具 | 版本要求 | 说明 |
|------|---------|------|
| **Node.js** | >= 18.0.0 | 前端运行环境 |
| **Python** | >= 3.11 | 后端运行环境 |
| **uv** | 最新版 | Python包管理器 |
| **FFmpeg** | 最新版 | 视频处理核心 |
| **Docker** | 最新版 | 基础设施服务 |

### 硬件建议

- **CPU**: 4核心及以上
- **内存**: 8GB及以上（推荐16GB）
- **存储**: 20GB可用空间
- **GPU**: 可选，用于加速字幕生成

---

## 🔑 API平台注册

本项目依赖第三方AI模型，需要注册以下平台：

### 1. 硅基流动（推荐）

**用途**: TTS语音合成、大模型服务

- 注册链接：[https://cloud.siliconflow.cn/i/63zI7Mdc](https://cloud.siliconflow.cn/i/63zI7Mdc)
- 服务：
  - index-tts2：高质量中文TTS
  - GPT-4o系列：大模型服务
  - Flux/SDXL：图片生成

### 2. 第三方中转平台（低成本）

**用途**: 低成本图片生成

- 注册链接：[https://api.vectorengine.ai/register?aff=YVx7](https://api.vectorengine.ai/register?aff=YVx7)
- 服务：Sora_Image（约0.04元/张）
- ⚠️ **注意**：按需充值，用多少充多少

### 3. 其他可选平台

- **OpenAI**: GPT-4o系列模型
- **Anthropic**: Claude 3.5系列模型
- **DeepSeek**: 高性价比大模型

---

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/869413421/aicon2.git
cd aicon2
```

### 2. 安装系统依赖

#### FFmpeg（视频处理核心）

```bash
# Windows (Chocolatey)
choco install ffmpeg

# Windows (Scoop)
scoop install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install epel-release && sudo yum install ffmpeg
```

验证安装：
```bash
ffmpeg -version
```

#### uv（Python包管理器）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用pip
pip install uv
```

验证安装：
```bash
uv --version
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env  # 或使用其他编辑器
```

**关键配置项**：

```bash
# 数据库配置
DATABASE_URL=postgresql://aicg:aicg123@localhost:5432/aicg

# Redis配置
REDIS_URL=redis://localhost:6379/0

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=aicg

# JWT密钥（请修改为随机字符串）
SECRET_KEY=your-secret-key-here

# API密钥（在系统中配置，这里可留空）
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
```

### 4. 启动基础设施

使用Docker Compose启动PostgreSQL、Redis、MinIO：

```bash
# 启动所有基础设施服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

或使用快捷脚本：
```bash
./scripts/start.sh
```

验证服务：
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)

### 5. 初始化后端

```bash
cd backend

# 安装Python依赖
uv sync

# 运行数据库迁移
alembic upgrade head

# 启动后端API服务
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

验证后端：访问 http://localhost:8000/docs 查看API文档

### 6. 启动Celery Worker

在新终端窗口中：

```bash
cd backend

# 启动Celery Worker
uv run celery -A src.tasks.task worker --loglevel=info
```

### 7. 启动前端

在新终端窗口中：

```bash
cd frontend

# 安装Node依赖
npm install

# 启动开发服务器
npm run dev
```

验证前端：访问 http://localhost:3000

---

## 🚀 高级配置

### GPU加速配置（可选）

如果您有NVIDIA GPU并希望加速视频字幕生成（faster-whisper），可以启用GPU支持。

**适用环境**: Linux / WSL

**前置条件**:
- NVIDIA GPU（支持CUDA）
- 已安装CUDA驱动

#### 安装步骤

1. **安装GPU版本依赖**

```bash
cd backend
uv pip install .[gpu] -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. **设置CUDA动态库路径**

激活虚拟环境后，设置环境变量：
```bash
source .venv/bin/activate
export LD_LIBRARY_PATH="<PROJECT_PATH>/.venv/lib/python3.12/site-packages/nvidia/cublas/lib:<PROJECT_PATH>/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
```

将 `<PROJECT_PATH>` 替换为实际项目路径。

3. **自动加载配置（推荐）**

将以下内容追加到 `.venv/bin/activate`，每次激活虚拟环境自动启用GPU：
```bash
export LD_LIBRARY_PATH="<PROJECT_PATH>/.venv/lib/python3.12/site-packages/nvidia/cublas/lib:<PROJECT_PATH>/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
```

4. **修改Whisper服务配置**

编辑 `backend/src/services/faster_whisper_service.py`：
```python
class WhisperTranscriptionService:
    def __init__(self, model_size="small", device="cuda", compute_type="float32"):
        """初始化语音识别服务"""
        logger.info(f"🔄 正在加载 Whisper 模型: {model_size} ...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.cc = OpenCC("t2s")
        logger.info(f"✅ 模型加载完成")
```

将 `device` 参数从 `"cpu"` 改为 `"cuda"`，`model_size` 可根据显存调整（tiny/base/small/medium/large）。

**性能提升**: GPU加速可将字幕生成速度提升3-10倍，具体取决于GPU型号。

---

### Bilibili发布工具配置（可选）

如果需要将生成的视频发布到Bilibili，需要部署biliup-rs工具。

#### 下载biliup-rs

**Linux/WSL**:
```bash
cd backend
mkdir -p bin
cd bin

# 下载 v0.2.4 的压缩包
wget https://github.com/biliup/biliup-rs/releases/download/v0.2.4/biliupR-v0.2.4-x86_64-linux.tar.xz

# 解压
tar -xvf biliupR-v0.2.4-x86_64-linux.tar.xz

# 移动并赋权
mv biliupR-v0.2.4-x86_64-linux/biliup biliup
chmod +x biliup
```

**Windows (PowerShell)**:
```powershell
cd backend
New-Item -ItemType Directory -Force -Path bin
cd bin

# 手动下载 v0.2.4 Windows 版本：
# https://github.com/biliup/biliup-rs/releases/download/v0.2.4/biliupR-v0.2.4-x86_64-windows.zip
# 解压后将 biliup.exe 放到 bin 目录
```

#### 创建Cookie存储目录

```bash
cd backend
mkdir -p data/bilibili_cookies
```

#### 验证安装

```bash
# Linux/WSL
./bin/biliup --version

# Windows
.\bin\biliup.exe --version
```

#### 使用说明

1. 通过API `/api/v1/bilibili/login/qrcode` 扫码登录B站
2. 调用 `/api/v1/bilibili/publish` 发布视频到B站
3. 支持自定义分区、标签、封面等配置

详细文档参见: [Bilibili发布集成方案](bilibili_integration_plan.md)

---

## 🐳 Docker部署（可选）

### 完整Docker部署

```bash
# 启动所有服务（包括后端和前端）
docker-compose -f docker-compose.full.yml up -d

# 查看服务状态
docker-compose -f docker-compose.full.yml ps

# 查看日志
docker-compose -f docker-compose.full.yml logs -f

# 停止服务
docker-compose -f docker-compose.full.yml down
```

### 仅基础设施

```bash
# 仅启动PostgreSQL、Redis、MinIO
docker-compose up -d

# 停止服务
docker-compose down
```

---

## ✅ 验证安装

### 检查服务状态

1. **前端应用**: http://localhost:3000
   - 应该能看到登录页面
   
2. **API文档**: http://localhost:8000/docs
   - 应该能看到FastAPI自动生成的API文档
   
3. **MinIO控制台**: http://localhost:9001
   - 用户名: minioadmin
   - 密码: minioadmin123

### 测试完整流程

1. 注册/登录账号
2. 配置API密钥
3. 创建项目并上传文本
4. 生成素材
5. 合成视频

---

## 🔧 常见问题

### Q: FFmpeg未找到

**A**: 确保FFmpeg已正确安装并添加到系统PATH。运行 `ffmpeg -version` 验证。

### Q: 数据库连接失败

**A**: 
1. 检查Docker服务是否正常运行：`docker-compose ps`
2. 检查.env文件中的数据库配置
3. 尝试重启Docker服务：`docker-compose restart`

### Q: MinIO连接失败

**A**:
1. 检查MinIO服务状态
2. 确认.env中的MinIO配置正确
3. 检查防火墙设置

### Q: Celery Worker无法启动

**A**:
1. 确保Redis服务正常运行
2. 检查.env中的Redis配置
3. 查看Celery日志获取详细错误信息

### Q: 前端无法连接后端

**A**:
1. 确认后端服务正常运行（http://localhost:8000/docs）
2. 检查前端的API配置（.env或vite.config.js）
3. 检查CORS配置

---

## 📞 获取帮助

如果遇到问题：

1. 查看[常见问题](#常见问题)
2. 查看项目Issues: https://github.com/869413421/aicon2/issues
3. 提交新Issue并附上详细错误信息

---

## 🔄 更新升级

```bash
# 拉取最新代码
git pull origin main

# 更新后端依赖
cd backend && uv sync

# 运行数据库迁移
alembic upgrade head

# 更新前端依赖
cd frontend && npm install

# 重启服务
```
