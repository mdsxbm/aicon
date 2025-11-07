# Data Model Specification: AICG内容分发平台

**Created**: 2025-11-06
**Purpose**: 定义完整的数据模型和关系结构
**ORM**: SQLAlchemy 2.0 (Async)
**Database**: PostgreSQL 15+

## 模型设计原则

### 命名规范
- 表名：蛇形命名法 (snake_case)
- 字段名：蛇形命名法
- 主键：UUID字符串 (id)
- 外键：关联表名 + _id
- 时间字段：created_at, updated_at

### 索引策略
- 主键自动索引
- 外键索引（无约束）
- 查询频繁字段单列索引
- 避免过度复合索引，保持简单高效

### 数据类型
- 主键：String (UUID)
- 文本内容：Text
- 状态：Enum
- 时间：DateTime (ISO8601格式，API中返回为字符串)
- 数量：Integer
- 金额：Decimal(10, 2)
- 时间轴：Float (秒，精确到毫秒)

## 核心数据模型

### 1. 用户模型 (User)

```python
# models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class User(Base):
    """用户模型 - 单一用户模式"""
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # 状态和权限
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)

    # 设置和偏好
    preferences = Column(Text, nullable=True)  # JSON格式存储偏好设置
    timezone = Column(String(50), default='Asia/Shanghai')
    language = Column(String(10), default='zh-CN')

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    api_configs = relationship("APIConfig", back_populates="user", cascade="all, delete-orphan")
    publication_records = relationship("PublicationRecord", back_populates="user")
```

### 2. 项目模型 (Project)

```python
# models/project.py
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

class ProjectStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class Project(Base):
    """项目模型 - 关联源文本文件"""
    __tablename__ = 'projects'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, nullable=False, index=True)  # 外键索引，无约束
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 文件信息
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_type = Column(String(10), nullable=False)  # txt, md, docx, epub
    file_path = Column(String(500), nullable=False)  # MinIO存储路径
    file_hash = Column(String(64), nullable=True, index=True)  # 文件MD5哈希

    # 统计信息
    word_count = Column(Integer, default=0)
    chapter_count = Column(Integer, default=0)
    paragraph_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)

    # 处理状态
    status = Column(String(20), default=ProjectStatus.UPLOADED, index=True)
    processing_progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)

    # 生成配置
    generation_settings = Column(Text, nullable=True)  # JSON格式存储生成配置

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系定义
    owner = relationship("User", back_populates="projects")
    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    generation_tasks = relationship("GenerationTask", back_populates="project", cascade="all, delete-orphan")

    # 索引定义
    __table_args__ = (
        Index('idx_project_owner', 'owner_id'),
        Index('idx_project_status', 'status'),
        Index('idx_project_created', 'created_at'),
        Index('idx_project_file_hash', 'file_hash'),
    )
```

### 3. 章节模型 (Chapter)

```python
# models/chapter.py
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

class ChapterStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Chapter(Base):
    """章节模型 - 文档的逻辑分割单元"""
    __tablename__ = 'chapters'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False, index=True)  # 外键索引，无约束
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # 章节原始内容

    # 结构信息
    chapter_number = Column(Integer, nullable=False)
    word_count = Column(Integer, default=0)
    paragraph_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)

    # 处理状态
    status = Column(String(20), default=ChapterStatus.PENDING, index=True)
    is_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime, nullable=True)

    # 编辑信息
    edited_content = Column(Text, nullable=True)  # 用户编辑后的内容
    editing_notes = Column(Text, nullable=True)  # 编辑备注

    # 生成信息
    generation_settings = Column(Text, nullable=True)  # 章节级生成配置
    video_url = Column(String(500), nullable=True)  # 最终视频URL
    video_duration = Column(Integer, nullable=True)  # 视频时长（秒）

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    project = relationship("Project", back_populates="chapters")
    paragraphs = relationship("Paragraph", back_populates="chapter", cascade="all, delete-orphan")
    generation_tasks = relationship("GenerationTask", back_populates="chapter", cascade="all, delete-orphan")
    publication_records = relationship("PublicationRecord", back_populates="chapter")

    # 索引定义
    __table_args__ = (
        Index('idx_chapter_project', 'project_id'),
        Index('idx_chapter_status', 'status'),
        Index('idx_chapter_number', 'chapter_number'),
    )
```

### 4. 段落模型 (Paragraph)

```python
# models/paragraph.py
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

class ParagraphAction(str, Enum):
    KEEP = "keep"
    EDIT = "edit"
    DELETE = "delete"
    IGNORE = "ignore"

class Paragraph(Base):
    """段落模型 - 章节内的文本段落"""
    __tablename__ = 'paragraphs'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = Column(String, nullable=False, index=True)  # 外键索引，无约束
    content = Column(Text, nullable=False)

    # 结构信息
    order_index = Column(Integer, nullable=False)  # 在章节中的顺序
    word_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)

    # 编辑控制
    action = Column(String(10), default=ParagraphAction.KEEP, index=True)
    edited_content = Column(Text, nullable=True)  # 编辑后的内容
    is_confirmed = Column(Boolean, default=False)
    ignore_reason = Column(Text, nullable=True)  # 忽略原因

    # 生成信息
    audio_url = Column(String(500), nullable=True)  # 段落音频URL
    audio_duration = Column(Integer, nullable=True)  # 音频时长（秒）

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    chapter = relationship("Chapter", back_populates="paragraphs")
    sentences = relationship("Sentence", back_populates="paragraph", cascade="all, delete-orphan")

    # 索引定义
    __table_args__ = (
        Index('idx_paragraph_chapter', 'chapter_id'),
        Index('idx_paragraph_order', 'order_index'),
        Index('idx_paragraph_action', 'action'),
        Index('idx_paragraph_confirmed', 'is_confirmed'),
    )
```

### 5. 句子模型 (Sentence)

```python
# models/sentence.py
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

class SentenceStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Sentence(Base):
    """句子模型 - 最小视频生成单元"""
    __tablename__ = 'sentences'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paragraph_id = Column(String, nullable=False, index=True)  # 外键索引，无约束
    content = Column(Text, nullable=False)

    # 结构信息
    order_index = Column(Integer, nullable=False)  # 在段落中的顺序
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)

    # 生成资源
    image_url = Column(String(500), nullable=True)  # 生成的图片URL
    image_prompt = Column(Text, nullable=True)  # 图片生成提示词
    audio_url = Column(String(500), nullable=True)  # 生成的音频URL

    # 时间轴信息（来自ASR）
    start_time = Column(Float, nullable=True)  # 音频开始时间（秒）
    end_time = Column(Float, nullable=True)  # 音频结束时间（秒）
    duration = Column(Float, nullable=True)  # 音频时长（秒）
    confidence_score = Column(Float, nullable=True)  # ASR置信度

    # 语音设置
    voice_settings = Column(Text, nullable=True)  # JSON格式的语音合成参数
    voice_type = Column(String(50), nullable=True)
    speech_rate = Column(Float, default=1.0)
    pitch = Column(Float, default=1.0)
    volume = Column(Float, default=1.0)

    # 处理状态
    status = Column(String(20), default=SentenceStatus.PENDING, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # 用户编辑
    edited_content = Column(Text, nullable=True)
    edited_prompt = Column(Text, nullable=True)
    is_manual_edited = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系定义
    paragraph = relationship("Paragraph", back_populates="sentences")

    # 索引定义
    __table_args__ = (
        Index('idx_sentence_paragraph', 'paragraph_id'),
        Index('idx_sentence_order', 'order_index'),
        Index('idx_sentence_status', 'status'),
        Index('idx_sentence_start_time', 'start_time'),
        Index('idx_sentence_end_time', 'end_time'),
    )
```

### 6. 生成任务模型 (GenerationTask)

```python
# models/generation_task.py
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GenerationStep(str, Enum):
    INITIALIZING = "initializing"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    TIMELINE_PROCESSING = "timeline_processing"
    VIDEO_SYNTHESIS = "video_synthesis"
    FINALIZING = "finalizing"

class GenerationTask(Base):
    """生成任务模型 - 视频生成的工作单元"""
    __tablename__ = 'generation_tasks'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, nullable=False, index=True)
    chapter_id = Column(String, nullable=False, index=True)
    api_config_id = Column(String, nullable=False, index=True)

    # 任务状态
    status = Column(String(20), default=TaskStatus.PENDING, index=True)
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(50), default=GenerationStep.INITIALIZING)
    priority = Column(Integer, default=0)  # 任务优先级

    # 进度统计
    total_sentences = Column(Integer, default=0)
    completed_sentences = Column(Integer, default=0)
    failed_sentences = Column(Integer, default=0)
    skipped_sentences = Column(Integer, default=0)

    # 时间信息
    estimated_duration = Column(Integer, nullable=True)  # 预估时长（分钟）
    estimated_completion = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 配置信息
    generation_settings = Column(Text, nullable=True)  # JSON格式的生成配置
    video_settings = Column(Text, nullable=True)  # 视频参数设置

    # 错误处理
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)  # JSON格式的详细错误信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 结果信息
    video_url = Column(String(500), nullable=True)
    video_size = Column(Integer, nullable=True)  # 视频文件大小（字节）
    video_duration = Column(Integer, nullable=True)  # 视频时长（秒）
    subtitle_url = Column(String(500), nullable=True)

    # 资源统计
    images_generated = Column(Integer, default=0)
    audio_segments_generated = Column(Integer, default=0)
    processing_time = Column(Integer, default=0)  # 处理时间（秒）

    # 控制标志
    is_paused = Column(Boolean, default=False)
    is_cancelled = Column(Boolean, default=False)
    auto_retry = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    project = relationship("Project", back_populates="generation_tasks")
    chapter = relationship("Chapter", back_populates="generation_tasks")
    api_config = relationship("APIConfig", back_populates="generation_tasks")

    # 索引定义
    __table_args__ = (
        Index('idx_task_project', 'project_id'),
        Index('idx_task_chapter', 'chapter_id'),
        Index('idx_task_status', 'status'),
        Index('idx_task_priority', 'priority'),
        Index('idx_task_created', 'created_at'),
    )
```

### 7. API配置模型 (APIConfig)

```python
# models/api_config.py
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Boolean, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

class ServiceType(str, Enum):
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    TRANSLATION = "translation"
    VIDEO_SYNTHESIS = "video_synthesis"

class ProviderType(str, Enum):
    VOLCENGINE = "volcengine"
    OPENAI = "openai"
    AZURE = "azure"
    GOOGLE = "google"
    BAIDU = "baidu"
    ALIBABA = "alibaba"
    CUSTOM = "custom"

class APIConfig(Base):
    """API配置模型 - AI服务的配置信息"""
    __tablename__ = 'api_configs'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(100), nullable=False)  # 配置名称
    provider = Column(String(50), nullable=False, index=True)
    service_type = Column(String(30), nullable=False, index=True)

    # API信息
    api_key = Column(String(500), nullable=False)  # 加密存储
    api_secret = Column(String(500), nullable=True)  # 加密存储
    endpoint = Column(String(500), nullable=True)
    region = Column(String(50), nullable=True)

    # 配置状态
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)  # 是否为默认配置
    is_verified = Column(Boolean, default=False)  # 是否已验证
    last_verified = Column(DateTime, nullable=True)

    # 使用限制
    monthly_limit = Column(Integer, nullable=True)  # 月度限制
    daily_limit = Column(Integer, nullable=True)    # 日限制
    rate_limit = Column(Integer, nullable=True)     # 每分钟限制

    # 使用统计
    current_usage = Column(Integer, default=0)
    total_usage = Column(Integer, default=0)
    cost_this_month = Column(Numeric(10, 2), default=0.00)
    total_cost = Column(Numeric(10, 2), default=0.00)

    # 使用记录
    last_used = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)

    # 配置参数
    config_params = Column(Text, nullable=True)  # JSON格式的配置参数
    pricing_model = Column(Text, nullable=True)  # JSON格式的计费模型

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # API密钥过期时间

    # 关系定义
    user = relationship("User", back_populates="api_configs")
    generation_tasks = relationship("GenerationTask", back_populates="api_config")

    # 索引定义
    __table_args__ = (
        Index('idx_api_user_provider', 'user_id', 'provider'),
        Index('idx_api_service_active', 'service_type', 'is_active'),
        Index('idx_api_user_active', 'user_id', 'is_active'),
        Index('idx_api_provider_service', 'provider', 'service_type'),
    )
```

### 8. 发布记录模型 (PublicationRecord)

```python
# models/publication_record.py
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

class PlatformType(str, Enum):
    BILIBILI = "bilibili"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    WEIBO = "weibo"
    XIAOHONGSHU = "xiaohongshu"

class PublicationStatus(str, Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VisibilityType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"
    SCHEDULED = "scheduled"

class PublicationRecord(Base):
    """发布记录模型 - 视频发布的操作记录"""
    __tablename__ = 'publication_records'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    chapter_id = Column(String, nullable=True, index=True)  # 章节级发布
    video_id = Column(String, nullable=False, index=True)   # 视频ID
    platform = Column(String(20), nullable=False, index=True)

    # 平台信息
    platform_account_id = Column(String(100), nullable=True)  # 平台账号ID
    platform_video_id = Column(String(200), nullable=True)   # 平台视频ID
    platform_url = Column(String(500), nullable=True)        # 平台视频链接

    # 发布内容
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON数组格式
    thumbnail_url = Column(String(500), nullable=True)

    # 发布设置
    visibility = Column(String(20), default=VisibilityType.PUBLIC)
    allow_comments = Column(Boolean, default=True)
    allow_download = Column(Boolean, default=True)
    age_restriction = Column(Boolean, default=False)

    # 定时发布
    is_scheduled = Column(Boolean, default=False)
    scheduled_at = Column(DateTime, nullable=True)

    # 发布状态
    status = Column(String(20), default=PublicationStatus.PENDING, index=True)
    progress = Column(Integer, default=0)  # 发布进度 0-100

    # 平台响应
    platform_response = Column(Text, nullable=True)  # 平台返回信息
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # 数据统计
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # 同步状态
    stats_last_updated = Column(DateTime, nullable=True)
    sync_enabled = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # 关系定义
    user = relationship("User", back_populates="publication_records")
    chapter = relationship("Chapter", back_populates="publication_records")

    # 索引定义
    __table_args__ = (
        Index('idx_publication_user_status', 'user_id', 'status'),
        Index('idx_publication_platform_status', 'platform', 'status'),
        Index('idx_publication_chapter_status', 'chapter_id', 'status'),
        Index('idx_publication_scheduled', 'is_scheduled', 'scheduled_at'),
        Index('idx_publication_created', 'created_at'),
    )
```

## 辅助数据模型

### 9. 时间轴模型 (Timeline)

```python
# models/timeline.py
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class Timeline(Base):
    """时间轴模型 - 视频时间轴信息"""
    __tablename__ = 'timelines'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = Column(String, nullable=False, index=True)

    # 时间轴信息
    total_duration = Column(Float, nullable=False)  # 总时长（秒）
    fps = Column(Integer, default=30)  # 帧率
    resolution = Column(String(20), default='1920x1080')

    # 时间轴数据
    timeline_data = Column(Text, nullable=False)  # JSON格式的时间轴数据

    # 音频轨道
    audio_track_url = Column(String(500), nullable=True)
    audio_duration = Column(Float, nullable=True)
    audio_sample_rate = Column(Integer, nullable=True)

    # 字幕轨道
    subtitle_track_url = Column(String(500), nullable=True)
    subtitle_format = Column(String(10), default='srt')

    # 背景音乐
    background_music_url = Column(String(500), nullable=True)
    background_music_volume = Column(Float, default=0.1)

    # 处理信息
    processing_status = Column(String(20), default='pending')
    error_message = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    chapter = relationship("Chapter")

    # 索引定义
    __table_args__ = (
        Index('idx_timeline_chapter', 'chapter_id'),
        Index('idx_timeline_status', 'processing_status'),
    )
```

### 10. 系统日志模型 (SystemLog)

```python
# models/system_log.py
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from datetime import datetime
import uuid
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(str, Enum):
    SYSTEM = "system"
    API = "api"
    TASK = "task"
    USER = "user"
    SECURITY = "security"

class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = 'system_logs'

    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # 日志信息
    level = Column(String(20), nullable=False, index=True)
    category = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # 关联信息
    user_id = Column(String, nullable=True, index=True)
    task_id = Column(String, nullable=True, index=True)
    request_id = Column(String(100), nullable=True, index=True)

    # 上下文信息
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)

    # 详细数据
    context_data = Column(Text, nullable=True)  # JSON格式的上下文数据
    stack_trace = Column(Text, nullable=True)

    # 性能信息
    execution_time = Column(Integer, nullable=True)  # 执行时间（毫秒）
    memory_usage = Column(Integer, nullable=True)    # 内存使用（字节）

    # 网络信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # 索引定义
    __table_args__ = (
        Index('idx_log_timestamp_level', 'timestamp', 'level'),
        Index('idx_log_category_timestamp', 'category', 'timestamp'),
        Index('idx_log_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_log_task_timestamp', 'task_id', 'timestamp'),
        Index('idx_log_request_id', 'request_id'),
    )
```

## 时间字段处理规范

### 时间格式统一
- **数据库存储**: PostgreSQL DateTime 类型
- **API响应**: ISO8601 字符串格式 (YYYY-MM-DDTHH:MM:SS.sssZ)
- **前端处理**: JavaScript Date 对象或字符串
- **时区**: 统一使用 UTC，前端根据用户时区转换

### 时间字段分类
- **创建时间**: `created_at` - 记录创建时间
- **更新时间**: `updated_at` - 记录最后修改时间
- **业务时间**: `started_at`, `completed_at`, `published_at` - 业务流程时间点
- **时间轴**: `start_time`, `end_time` - 音视频时间轴（Float类型，秒）

### 时间轴特殊处理
- 音频时间轴使用 Float 类型存储秒数（精确到毫秒）
- ASR识别的时间戳用于字幕同步
- 视频合成时转换为时间码格式

## 数据库初始化

### 基础模型类

```python
# models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime
from datetime import datetime
import uuid

Base = declarative_base()

class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class UUIDMixin:
    """UUID主键混入类"""
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)

class SoftDeleteMixin:
    """软删除混入类"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)
```

### 数据库连接配置

```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/aicg_db")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    async_native=True,
)

# 创建会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 获取数据库会话
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

## 数据迁移

### Alembic配置

```python
# migrations/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from models.base import Base
from core.config import settings

# 导入所有模型
from models import user, project, chapter, paragraph, sentence, generation_task, api_config, publication_record

target_metadata = Base.metadata

def run_migrations_online():
    """在线模式运行迁移"""
    configuration = context.config
    configuration.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    connectable = engine_from_config(
        configuration.get_section(configuration.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

---

**模型版本**: 1.0.0
**最后更新**: 2025-11-06
**兼容性**: PostgreSQL 15+, SQLAlchemy 2.0+