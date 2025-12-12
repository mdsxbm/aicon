# 💻 开发指南

本文档提供AICG平台的开发环境搭建和开发规范说明。

---

## 🏗️ 项目结构

```
aicon2/
├── backend/                 # Python/FastAPI后端
│   ├── src/
│   │   ├── api/            # API路由
│   │   │   ├── v1/         # API v1版本
│   │   │   ├── dependencies.py  # 依赖注入
│   │   │   └── schemas/    # Pydantic模型
│   │   ├── models/         # SQLAlchemy数据模型
│   │   ├── services/       # 业务逻辑层
│   │   ├── tasks/          # Celery异步任务
│   │   ├── utils/          # 工具函数
│   │   ├── core/           # 核心配置
│   │   └── main.py         # FastAPI应用入口
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 测试
│   ├── bin/                # 二进制工具（biliup等）
│   ├── data/               # 数据文件
│   └── pyproject.toml      # Python项目配置
├── frontend/               # Vue.js前端
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── composables/    # 组合式API
│   │   ├── services/       # API服务
│   │   ├── stores/         # Pinia状态管理
│   │   ├── views/          # 页面视图
│   │   ├── router/         # 路由配置
│   │   ├── assets/         # 静态资源
│   │   └── App.vue         # 根组件
│   ├── public/             # 公共资源
│   └── package.json        # Node项目配置
├── docs/                   # 文档
│   ├── media/              # 产品演示GIF
│   ├── INSTALLATION.md     # 安装指南
│   ├── DEVELOPMENT.md      # 开发指南
│   └── FEATURES.md         # 功能说明
├── scripts/                # 运维脚本
├── docker-compose.yml      # Docker编排
└── .env.example           # 环境变量模板
```

---

## 🛠️ 开发环境搭建

### 后端开发环境

#### 1. 安装依赖

```bash
cd backend

# 使用uv安装依赖
uv sync

# 或使用pip
pip install -e .
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env
```

#### 3. 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# 创建初始数据（可选）
uv run python scripts/init_db.py
```

#### 4. 启动开发服务器

```bash
# 启动FastAPI服务（带热重载）
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker
uv run celery -A src.tasks.task worker --loglevel=info
```

### 前端开发环境

#### 1. 安装依赖

```bash
cd frontend

# 使用npm安装
npm install

# 或使用pnpm（推荐）
pnpm install
```

#### 2. 配置环境变量

前端环境变量在 `.env` 或 `vite.config.js` 中配置：

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

#### 3. 启动开发服务器

```bash
# 启动Vite开发服务器
npm run dev

# 或使用pnpm
pnpm dev
```

---

## 📝 代码规范

### Python代码规范

遵循 **PEP 8** 规范：

```python
# 导入顺序：标准库 -> 第三方库 -> 本地模块
import os
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.core.database import get_db

# 使用类型注解
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取用户信息"""
    pass

# 使用docstring
class UserService:
    """用户服务类
    
    提供用户相关的业务逻辑处理
    """
    
    async def create_user(self, username: str) -> User:
        """创建新用户
        
        Args:
            username: 用户名
            
        Returns:
            创建的用户对象
            
        Raises:
            ValueError: 用户名已存在
        """
        pass
```

### JavaScript/Vue代码规范

遵循 **Vue 3 风格指南**：

```javascript
// 使用组合式API
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// Props定义
const props = defineProps({
  userId: {
    type: String,
    required: true
  }
})

// Emits定义
const emit = defineEmits(['update', 'delete'])

// 响应式数据
const user = ref(null)
const loading = ref(false)

// 计算属性
const displayName = computed(() => {
  return user.value?.display_name || user.value?.username
})

// 方法
const fetchUser = async () => {
  loading.value = true
  try {
    const response = await userService.getUser(props.userId)
    user.value = response
  } catch (error) {
    console.error('获取用户失败:', error)
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  fetchUser()
})
</script>
```

---

## 🗄️ 数据库迁移

### 创建迁移

```bash
cd backend

# 自动生成迁移文件
alembic revision --autogenerate -m "描述迁移内容"

# 手动创建迁移文件
alembic revision -m "描述迁移内容"
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>

# 回退一个版本
alembic downgrade -1

# 回退到指定版本
alembic downgrade <revision_id>
```

### 查看迁移历史

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看详细历史
alembic history --verbose
```

---

## 🧪 测试

### 后端测试

```bash
cd backend

# 运行所有测试
uv run pytest

# 运行指定测试文件
uv run pytest tests/test_user.py

# 运行指定测试函数
uv run pytest tests/test_user.py::test_create_user

# 生成覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 前端测试

```bash
cd frontend

# 运行单元测试
npm run test:unit

# 运行E2E测试
npm run test:e2e

# 生成覆盖率报告
npm run test:coverage
```

---

## 🔧 常用命令

### 后端命令

| 命令 | 描述 |
|------|------|
| `uv sync` | 安装/更新依赖 |
| `uv run uvicorn src.main:app --reload` | 启动开发服务器 |
| `uv run celery -A src.tasks.task worker` | 启动Celery Worker |
| `alembic upgrade head` | 运行数据库迁移 |
| `uv run pytest` | 运行测试 |
| `uv run black src/` | 格式化代码 |
| `uv run ruff check src/` | 代码检查 |

### 前端命令

| 命令 | 描述 |
|------|------|
| `npm install` | 安装依赖 |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |
| `npm run lint` | 代码检查 |
| `npm run format` | 格式化代码 |

### Docker命令

| 命令 | 描述 |
|------|------|
| `docker-compose up -d` | 启动服务 |
| `docker-compose down` | 停止服务 |
| `docker-compose ps` | 查看服务状态 |
| `docker-compose logs -f` | 查看日志 |
| `docker-compose restart` | 重启服务 |
| `docker-compose exec backend bash` | 进入后端容器 |

---

## 🐛 调试技巧

### 后端调试

#### 使用Python调试器

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用ipdb（更友好）
import ipdb; ipdb.set_trace()
```

#### 查看日志

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 前端调试

#### 使用Vue DevTools

安装Vue DevTools浏览器扩展，可以：
- 查看组件树
- 检查组件状态
- 追踪事件
- 性能分析

#### 使用console调试

```javascript
// 打印变量
console.log('变量值:', variable)

// 打印对象
console.table(arrayOfObjects)

// 性能测试
console.time('操作名称')
// ... 代码
console.timeEnd('操作名称')
```

---

## 📚 API文档

### 自动生成的API文档

FastAPI自动生成交互式API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API版本控制

API路由使用版本前缀：

```python
# backend/src/api/v1/users.py
router = APIRouter(prefix="/users", tags=["users"])

# 访问: /api/v1/users
```

---

## 🔐 安全最佳实践

### 1. 环境变量管理

- ✅ 使用 `.env` 文件存储敏感信息
- ✅ 不要提交 `.env` 到版本控制
- ✅ 使用强随机密钥

### 2. API密钥保护

- ✅ 加密存储API密钥
- ✅ 使用JWT认证
- ✅ 实施速率限制

### 3. 输入验证

- ✅ 使用Pydantic进行数据验证
- ✅ 防止SQL注入
- ✅ 防止XSS攻击

---

## 🚀 性能优化

### 后端优化

1. **数据库查询优化**
   - 使用索引
   - 避免N+1查询
   - 使用连接池

2. **异步处理**
   - 使用Celery处理耗时任务
   - 使用异步数据库操作

3. **缓存策略**
   - Redis缓存热点数据
   - 使用CDN加速静态资源

### 前端优化

1. **代码分割**
   - 路由懒加载
   - 组件懒加载

2. **资源优化**
   - 图片压缩
   - 使用WebP格式
   - 启用Gzip压缩

3. **性能监控**
   - 使用Lighthouse
   - 监控首屏加载时间

---

## 📖 学习资源

### 后端技术栈

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Celery文档](https://docs.celeryq.dev/)

### 前端技术栈

- [Vue 3官方文档](https://vuejs.org/)
- [Element Plus文档](https://element-plus.org/)
- [Pinia文档](https://pinia.vuejs.org/)

---

## 🤝 贡献指南

### 提交代码

1. Fork项目
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

### 提交规范

使用语义化提交信息：

```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建/工具变动
```

---

## 📞 获取帮助

- 查看[安装指南](INSTALLATION.md)
- 查看[功能说明](FEATURES.md)
- 提交Issue: https://github.com/869413421/aicon2/issues
