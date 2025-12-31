# 使用预构建镜像部署

## 快速开始

使用预构建镜像部署,无需本地编译,大大加快部署速度!

### 1. 克隆仓库

```bash
git clone https://github.com/869413421/aicon.git
cd aicon
```

### 2. 配置环境变量

复制环境变量模板:

```bash
cp .env.production.example .env.production
```

编辑 `.env.production`,设置必要的配置:
- 数据库密码
- Redis 密码
- MinIO 密码
- JWT 密钥
- 加密密钥

### 3. 启动服务

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**就这么简单!** 镜像会自动从 Docker Hub 拉取,无需等待编译。

### 4. 验证部署

检查服务状态:

```bash
docker-compose -f docker-compose.prod.yml ps
```

所有服务应该显示为 `healthy` 或 `running`。

## 访问服务

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📖 AI 电影使用指引

### 1. 注册获取 API Key
推荐使用中转站以获得更低成本和更强性能:
- **注册地址**: [https://api.aiconapi.me/](https://api.aiconapi.me/)
- 获取令牌后,在系统后台配置。

### 2. 系统配置
在系统的 **API密钥管理** 中添加:
- **供应商**: `自定义`
- **Base URL**: `https://api.aiconapi.me/v1` (**末尾不带斜杠**)
- **API密钥**: 填入你的令牌

### 3. 开始创作
1. **新建项目**: 选择“以章的方式”导入小说。
2. **进入工作室**: 进入项目详情 -> “电影工作室”。
3. **开始任务**: 按照顺序提取角色、场景、分镜,最后合成电影。

## 优势

✅ **快速部署**: 无需等待编译,直接拉取即用  
✅ **一致性**: 所有用户使用相同的预构建镜像  
✅ **节省资源**: 不需要本地构建环境  
✅ **简单易用**: 只需 3 个命令即可完成部署

## 故障排除

### 镜像拉取失败

如果拉取失败,可能是网络问题。可以配置 Docker 镜像加速器:

```bash
# 编辑 /etc/docker/daemon.json (Linux)
# 或 Docker Desktop 设置 (Windows/Mac)
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

### 服务启动失败

查看日志:

```bash
docker-compose -f docker-compose.prod.yml logs backend
```
